"""The shared layer (G0·C), called in-process (D-6), modelled on G2·C's adapter.

One adapter so every capability call goes through one place and is counted. Every method returns the capability's
typed `Output`; a `Refusal` becomes `Output(ok=False, error=…)` exactly as G0's MCP server does.

Two seeds are loaded through G0's own idempotent seed loader, because the v1 contracts have no register tool (D-7):
the rubric `g3_linkedin_post_v1` and the brand policy version `g3-skill-1` (D-4). The loader refuses anything not
namespaced `g3`, so G0's own rubrics and policy v1 can never be overwritten from here.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from pathlib import Path
from typing import Any

from pydantic import ValidationError
from shared_layer.capabilities import brand_policy, claims_registry, evaluation, measurement, observability
from shared_layer.capabilities import health as health_cap
from shared_layer.contracts import contract_versions
from shared_layer.errors import Refusal, ToolError
from shared_layer.storage import Database, open_database

from post_loop.models import REPO_DIR

RUBRIC_FILE = REPO_DIR / "rubrics" / "g3_linkedin_post_v1.json"
RUBRIC_ID = "g3_linkedin_post_v1"
BRAND_FILE = REPO_DIR / "brand" / "brand_policy_g3_skill_1.json"
BRAND_POLICY_VERSION = "g3-skill-1"
# Every draft must pass G0's own policy v1 AND the skill-seeded delta (D-4).
BRAND_VERSIONS = ("1", BRAND_POLICY_VERSION)


class LayerDegraded(RuntimeError):
    """health reported `degraded`, or a G3 seed is missing; the run must not start."""


class Layer:
    def __init__(self, db_path: str | None = None, db: Database | None = None,
                 rubric_file: Path | None = None, brand_file: Path | None = None) -> None:
        self.db = db or open_database(db_path)
        self.calls: Counter[str] = Counter()
        self.rubric_file = rubric_file or RUBRIC_FILE
        self.brand_file = brand_file or BRAND_FILE
        try:
            self.load_seeds()
        except Exception:
            self.db.close()
            raise

    def close(self) -> None:
        self.db.close()

    # -- the one way a call is made ------------------------------------------

    def _run(self, module: Any, **kwargs: Any) -> Any:
        self.calls[module.TOOL] += 1
        output_cls = module.Output
        try:
            inp = module.Input(**kwargs)
        except ValidationError as e:
            return output_cls(ok=False, error=ToolError(code="INVALID_ARGUMENT", message=str(e).splitlines()[0]))
        try:
            return module.run(self.db, inp)
        except Refusal as r:
            return output_cls(ok=False, error=r.envelope)
        except sqlite3.Error as e:
            return output_cls(ok=False, error=ToolError(code="STORAGE_ERROR", message=f"SQLite refused the operation: {e}"))

    # -- seeds (D-4, D-7) ------------------------------------------------------

    def load_seeds(self) -> None:
        rubric_doc = json.loads(self.rubric_file.read_text(encoding="utf-8"))
        ids = [r["id"] for r in rubric_doc["rubrics"]]
        if not ids or any(not i.startswith("g3_") for i in ids):
            raise LayerDegraded(f"this consumer may only seed rubrics namespaced g3_*, got {ids}")
        brand_doc = json.loads(self.brand_file.read_text(encoding="utf-8"))
        rule_ids = [r["id"] for r in brand_doc["rules"]]
        if not str(brand_doc["policy_version"]).startswith("g3-") or any(not i.startswith("g3.") for i in rule_ids):
            raise LayerDegraded(f"this consumer may only seed brand policy versions g3-* with rules g3.*, "
                                f"got {brand_doc['policy_version']!r} / {rule_ids}")
        with self.db.conn:
            self.db._seed_rubrics(rubric_doc)  # G0's own idempotent loader (INSERT OR REPLACE by id)
            self.db._seed_brand_policy(brand_doc)

    # -- capabilities ------------------------------------------------------------

    def health(self) -> health_cap.Output:
        self.calls[health_cap.TOOL] += 1
        return health_cap.run(self.db, health_cap.Input(), contracts=contract_versions())

    def require_healthy(self) -> health_cap.Output:
        h = self.health()
        if h.status != "ok":
            raise LayerDegraded(f"shared layer degraded: writable={h.db_writable} seeds={h.seeds} at {h.db_path}")
        if RUBRIC_ID not in h.rubrics:
            raise LayerDegraded(f"rubric {RUBRIC_ID} is not in the layer's store (have {h.rubrics})")
        missing = [v for v in BRAND_VERSIONS if v not in h.policy_versions]
        if missing:
            raise LayerDegraded(f"brand policy version(s) {missing} not in the layer's store (have {h.policy_versions})")
        return h

    def check_claims(self, text: str) -> claims_registry.Output:
        return self._run(claims_registry, text=text)

    def check_brand(self, text: str, channel: str = "linkedin", policy_version: str = "1") -> brand_policy.Output:
        return self._run(brand_policy, text=text, channel=channel, policy_version=policy_version)

    def brand_gate(self, text: str, channel: str = "linkedin") -> tuple[bool, list[Any]]:
        """Pass only when every policy version in `BRAND_VERSIONS` passes; refusals count as failures."""
        ok, violations = True, []
        for v in BRAND_VERSIONS:
            out = self.check_brand(text, channel=channel, policy_version=v)
            if not out.ok:
                raise LayerDegraded(f"brand_policy {v} refused: {out.error}")
            ok = ok and out.passed
            violations.extend(out.violations)
        return ok, violations

    def evaluate(self, item: str | dict[str, Any], *, rubric_id: str = RUBRIC_ID, context: str | None = None,
                 run_id: str | None = None, judge: str = "deterministic") -> evaluation.Output:
        return self._run(evaluation, rubric_id=rubric_id, item=item, context=context, judge=judge, run_id=run_id)

    def log_call(self, *, run_id: str, agent: str, step: str, model: str | None = None, input_tokens: int = 0, output_tokens: int = 0,
                 cost_usd: float = 0.0, status: str = "ok", duration_ms: int | None = None, note: str | None = None) -> observability.Output:
        return self._run(observability, run_id=run_id, agent=agent, step=step, model=model, input_tokens=input_tokens,
                         output_tokens=output_tokens, cost_usd=cost_usd, status=status, duration_ms=duration_ms, note=note)

    def run_total(self, run_id: str) -> observability.RunTotal:
        return observability.run_total(self.db, run_id)

    def record(self, event: str, fields: dict[str, Any], run_id: str, agent: str = "post-loop") -> measurement.Output:
        return self._run(measurement, event=event, fields=fields, run_id=run_id, agent=agent)

    # -- cost (G0's price table; this repo has none of its own) ------------------

    @staticmethod
    def cost_usd(model: str, input_tokens: int, output_tokens: int) -> float:
        p_in, p_out = dict(evaluation.PRICES_PER_MTOK).get(model, (0.0, 0.0))
        return round(float(input_tokens * p_in / 1e6 + output_tokens * p_out / 1e6), 6)

    @staticmethod
    def cap_usd() -> float:
        return float(observability.cap_usd())
