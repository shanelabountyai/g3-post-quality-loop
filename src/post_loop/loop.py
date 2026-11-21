"""The evaluator–optimizer loop (C5).

    health ─► for n in 1..cap:
                 draft  = Writer(source)            if n == 1 and no draft was supplied
                        = Writer(draft, fixes)      if the previous pass had a valid verdict
                        = unchanged                 if the previous Critic output was malformed (D-12)
                 raw    = Critic(source, draft)
                 verdict = parse_critic(raw)  ── invalid ─► pass logged as failed, continue (D-12)
                 gate   = G0: claims_registry + claim_rule_v1 + brand_policy(v1, g3-skill-1)
                          + evaluation(g3_linkedin_post_v1, {…, hook_score})            (D-8)
                 passed = verdict.pass AND gate passed                                     (D-10)
                 stop on passed
              ─► cap hit: needs_human_review = True                                       (D-13)

The loop never calls the Critic more than `cap` times (AC 2): the bound is the `for` statement, nothing else.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

import anyio

from post_loop.fixtures import Cases, load_cases
from post_loop.layer import Layer
from post_loop.llm import CallResult, ModelCaller, ModelCallError
from post_loop.models import Case, CriticOutputInvalid, CriticVerdict, DraftSource, LoopResult, PassRecord, Source, Stop, parse_critic
from post_loop.prompts import CRITIC, WRITER, AgentSpec, critic_input, writer_input

MAX_CAP_DEFAULT = 3  # D-2 (provisional)


class PostLoopError(RuntimeError):
    """The loop cannot run (bad cap, Writer output unusable)."""


@dataclass
class GateResult:
    claims_registry: str
    claims_detail: list[dict[str, Any]]
    claims_in_source: str
    brand: str
    brand_violations: list[dict[str, Any]]
    evaluation_id: str
    total: float
    criteria: list[dict[str, Any]]
    g0_passed: bool
    passed: bool
    fixes: list[str] = field(default_factory=list)


def gate(layer: Layer, *, draft: str, source: Source, critic: CriticVerdict, run_id: str) -> GateResult:
    """Every rule check for one draft, all in G0 (D-8). Returns the decision and the fixes G0 can name."""
    fixes: list[str] = []

    claims = layer.check_claims(draft)
    if not claims.ok:
        raise PostLoopError(f"claims_registry refused: {claims.error}")
    detail = [{"claim": r.claim, "status": r.status, "note": r.note} for r in claims.results]
    unsupported = [r for r in claims.results if r.status == "unsupported"]
    claims_registry = "unsupported" if unsupported else "clear"
    fixes += [f"Remove or correct this claim; the shared claims registry contradicts it: {r.claim!r} ({r.note})" for r in unsupported]

    rule = layer.evaluate(draft, rubric_id="claim_rule_v1", context=source.text, run_id=run_id)
    if not rule.ok:
        raise PostLoopError(f"evaluation claim_rule_v1 refused: {rule.error}")
    claims_in_source = "pass" if rule.passed else "fail"
    fixes += [f"Claim rule ({s.criterion}): {s.note}. Use only what the source note says." for s in rule.scores if s.score < 1.0]

    brand_ok, violations = layer.brand_gate(draft)
    brand = "pass" if brand_ok else "fail"
    fixes += [f"Brand ({v.rule_id}): {v.fix} [{v.excerpt}]" for v in violations]

    item = {"post": draft, "claims_registry": claims_registry, "claims_in_source": claims_in_source, "brand": brand,
            "hook_score": str(critic.scores.hook)}
    ev = layer.evaluate(item, run_id=run_id)
    if not ev.ok:
        raise PostLoopError(f"evaluation g3_linkedin_post_v1 refused: {ev.error}")
    return GateResult(
        claims_registry=claims_registry, claims_detail=detail, claims_in_source=claims_in_source, brand=brand,
        brand_violations=[v.model_dump() for v in violations], evaluation_id=ev.evaluation_id, total=ev.total,
        criteria=[s.model_dump() for s in ev.scores], g0_passed=ev.passed, passed=bool(ev.passed and critic.pass_), fixes=fixes,
    )


class PostLoop:
    def __init__(self, *, layer: Layer, caller: ModelCaller, cap: int = MAX_CAP_DEFAULT, run_id: str, cases: Cases | None = None) -> None:
        if cap < 1:
            raise PostLoopError(f"the pass cap must be at least 1, got {cap}")
        self.layer, self.caller, self.cap, self.run_id = layer, caller, cap, run_id
        self.cases = cases or load_cases()

    def run(self, case: Case) -> LoopResult:
        return anyio.run(self._run, case)

    # -- one model turn, logged in G0 observability --------------------------------

    async def _call(self, spec: AgentSpec, text: str, case: Case, n: int) -> tuple[CallResult, dict[str, Any]]:
        key = f"{spec.name}:{case.id}:{n}"
        r = await self.caller.call(spec, text, key)
        cost = self.layer.cost_usd(r.model, r.input_tokens, r.output_tokens) if self.caller.measured else 0.0
        log = self.layer.log_call(run_id=self.run_id, agent=spec.name, step=f"{case.id}:pass{n}", model=r.model,
                                  input_tokens=r.input_tokens, output_tokens=r.output_tokens, cost_usd=cost, duration_ms=r.duration_ms,
                                  note=None if self.caller.measured else "recorded response; usage not measured live")
        usage = {"model": r.model, "input_tokens": r.input_tokens, "output_tokens": r.output_tokens, "cost_usd": cost,
                 "measured": self.caller.measured, "over_cap": bool(getattr(log, "over_cap", False))}
        return r, usage

    @staticmethod
    def _post(r: CallResult) -> str:
        raw: Any = r.raw
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError as e:
                raise PostLoopError(f"Writer output is not JSON: {e.msg}") from e
        post = raw.get("post") if isinstance(raw, dict) else None
        if not isinstance(post, str) or not post.strip():
            raise PostLoopError("Writer output has no non-empty `post`")
        return post.strip()

    async def _run(self, case: Case) -> LoopResult:
        self.layer.require_healthy()  # health first; a degraded layer stops before any model call
        source = self.cases.source_for(case)
        draft: str | None = case.start_draft
        last_fixes: list[str] | None = None  # None = no trustworthy fixes from the previous pass
        passes: list[PassRecord] = []
        stop: Stop = "cap_hit"
        over_budget = False

        for n in range(1, self.cap + 1):
            usage: dict[str, dict[str, Any] | None] = {"writer": None, "critic": None}
            draft_source: DraftSource
            if draft is None:
                r, usage["writer"] = await self._call(WRITER, writer_input(source.title, source.text), case, n)
                draft, draft_source = self._post(r), "written"
            elif n == 1:
                draft_source = "supplied"
            elif last_fixes is not None:
                r, usage["writer"] = await self._call(WRITER, writer_input(source.title, source.text, draft, last_fixes), case, n)
                draft, draft_source = self._post(r), "revised"
            else:
                draft_source = "unchanged"

            cr, usage["critic"] = await self._call(CRITIC, critic_input(source.title, source.text, draft), case, n)
            over_budget = any(u and u["over_cap"] for u in usage.values())
            try:
                verdict = parse_critic(cr.raw)
            except CriticOutputInvalid as e:
                passes.append(PassRecord(n=n, draft=draft, draft_source=draft_source, critic_valid=False, critic_error=str(e),
                                         passed=False, usage=usage))
                last_fixes = None
                if over_budget:
                    break
                continue

            g = gate(self.layer, draft=draft, source=source, critic=verdict, run_id=self.run_id)
            fixes = list(verdict.fixes) + [f for f in g.fixes if f not in verdict.fixes]
            passes.append(PassRecord(
                n=n, draft=draft, draft_source=draft_source, critic_valid=True, critic=verdict,
                critic_overruled=bool(verdict.pass_ and not g.g0_passed),
                claims_registry=g.claims_registry, claims_detail=g.claims_detail,
                claims_in_source=g.claims_in_source, brand=g.brand, brand_violations=g.brand_violations,
                evaluation_id=g.evaluation_id, evaluation_total=g.total, criteria=g.criteria, passed=g.passed,
                fixes_for_next=[] if g.passed else fixes, usage=usage,
            ))
            if g.passed:
                stop = "passed"
                break
            last_fixes = fixes
            if over_budget:
                break

        if over_budget and stop != "passed":
            stop = "over_budget"
        passed = stop == "passed"
        tokens = {"input": 0, "output": 0}
        cost = 0.0
        for p in passes:
            for u in p.usage.values():
                if u:
                    tokens["input"] += int(u["input_tokens"])
                    tokens["output"] += int(u["output_tokens"])
                    cost += float(u["cost_usd"])
        result = LoopResult(
            run_id=self.run_id, case_id=case.id, source=source, cap=self.cap, passes=passes, passed=passed, stop_reason=stop,
            needs_human_review=not passed, final_draft=passes[-1].draft if passes else (draft or ""), caller=self.caller.name,
            measured=self.caller.measured, tokens=tokens, cost_usd=round(cost, 6),
        )
        self.layer.record("post_loop.finished", {"case": case.id, "passes": len(passes), "cap": self.cap, "passed": passed,
                                                 "needs_human_review": result.needs_human_review, "over_budget": over_budget},
                          run_id=self.run_id)
        return result


def run_case(layer: Layer, caller: ModelCaller, case: Case, *, run_id: str, cap: int = MAX_CAP_DEFAULT,
             cases: Cases | None = None) -> LoopResult:
    try:
        return PostLoop(layer=layer, caller=caller, cap=cap, run_id=run_id, cases=cases).run(case)
    except ModelCallError as e:
        raise PostLoopError(str(e)) from e
