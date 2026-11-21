"""Report (C8, D-15): average passes to pass and how often the cap is hit."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from post_loop.models import LoopResult


def summarize(results: list[LoopResult]) -> dict[str, Any]:
    passed = [r for r in results if r.passed]
    capped = [r for r in results if not r.passed]
    return {
        "cases": len(results),
        "passed": len(passed),
        "needs_human_review": len(capped),
        "avg_passes_to_pass": round(sum(len(r.passes) for r in passed) / len(passed), 2) if passed else None,
        "cap_hit_rate": round(len(capped) / len(results), 4) if results else None,
        "max_passes": max((len(r.passes) for r in results), default=0),
        "malformed_caught": sum(1 for r in results for p in r.passes if not p.critic_valid),
        "critic_overruled": sum(1 for r in results for p in r.passes if p.critic_overruled),
        "tokens": {"input": sum(r.tokens.get("input", 0) for r in results), "output": sum(r.tokens.get("output", 0) for r in results)},
        "cost_usd": round(sum(r.cost_usd for r in results), 6),
        "measured_live": bool(results) and all(r.measured for r in results),
    }


def build_report(results: list[LoopResult], *, run_id: str, cap: int) -> str:
    s = summarize(results)
    live = s["measured_live"]
    mode = "live (Claude Agent SDK)" if live else "recorded fixtures — hand-written responses, no model called; tokens and cost are **not measured live**"
    rate = f"{100 * s['cap_hit_rate']:.0f}%" if s["cap_hit_rate"] is not None else "n/a"
    lines = [
        "# Eval report — G3·C Post Quality Loop",
        "",
        f"Generated {datetime.now(UTC).isoformat(timespec='seconds')} · run `{run_id}` · pass cap {cap} · mode: {mode}.",
        "",
        "## Headline",
        "",
        f"- **Average passes to pass: {s['avg_passes_to_pass']}** (over the {s['passed']} cases that passed)",
        f"- **Cap-hit rate: {rate}** ({s['needs_human_review']} of {s['cases']} cases flagged *needs human review*)",
        f"- Most passes used by any case: {s['max_passes']} (cap {cap})",
        f"- Malformed Critic responses caught by schema validation: {s['malformed_caught']}",
        f"- Critic passes overruled by the shared layer (G0): {s['critic_overruled']}",
        f"- Tokens: {s['tokens']['input']} in / {s['tokens']['output']} out · cost ${s['cost_usd']:.4f}"
        + ("" if live else " — not measured live (no API key; recorded path, D-9)"),
        "",
    ]
    if not live:
        lines += [
            "> These numbers describe the hand-written fixtures in `fixtures/recorded.json`, which were written to exercise "
            "pass-on-1, pass-on-2, pass-on-3, a cap hit, an unsupported claim and malformed Critic output. They test the loop "
            "and the governed checks, not a model. A live run (NEXT.md, \"You:\" steps) produces the real numbers.",
            "",
        ]
    lines += ["## Per case", "", "| case | outcome | passes | hook by pass | brand by pass | G0 total by pass | notes |", "|---|---|---|---|---|---|---|"]
    for r in results:
        hooks = " → ".join(str(p.critic.scores.hook) if p.critic else "✗" for p in r.passes)
        brands = " → ".join(str(p.critic.scores.brand) if p.critic else "✗" for p in r.passes)
        totals = " → ".join(f"{p.evaluation_total:.2f}" if p.critic_valid else "✗" for p in r.passes)
        notes = []
        if any(not p.critic_valid for p in r.passes):
            notes.append(f"{sum(1 for p in r.passes if not p.critic_valid)} malformed Critic response(s) caught")
        if any(p.critic_overruled for p in r.passes):
            notes.append("Critic pass overruled by G0")
        if any(p.claims_registry == "unsupported" for p in r.passes):
            notes.append("registry: unsupported claim")
        if any(p.claims_in_source == "fail" for p in r.passes):
            notes.append("number not in source")
        if any(p.brand == "fail" for p in r.passes):
            rules = sorted({v["rule_id"] for p in r.passes for v in p.brand_violations})
            notes.append("brand: " + ", ".join(rules))
        outcome = "passed" if r.passed else "**needs human review**"
        lines.append(f"| `{r.case_id}` | {outcome} | {len(r.passes)} | {hooks} | {brands} | {totals} | {'; '.join(notes)} |")
    lines += ["", "✗ = the Critic's response failed schema validation; that pass failed closed (D-12).", ""]
    return "\n".join(lines)
