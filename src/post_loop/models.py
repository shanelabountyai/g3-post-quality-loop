"""Typed hand-offs and the Critic schema (D-11).

`CriticVerdict` is the contract the Critic must meet. Anything else — prose, broken JSON, a missing or extra
field, a score outside 1–5, a fail with no fixes, a pass that lists unsupported claims — raises
`CriticOutputInvalid` and is never treated as a verdict (AC 5).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

REPO_DIR = Path(__file__).resolve().parents[2]
FIXTURES_DIR = REPO_DIR / "fixtures"
SCHEMAS_DIR = REPO_DIR / "schemas"

Score = int


class CriticOutputInvalid(ValueError):
    """The Critic's response is not a valid `CriticVerdict`."""


class CriticScores(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    claims: Score = Field(ge=1, le=5, description="1–5: every factual claim is in the source note or the claims registry.")
    brand: Score = Field(ge=1, le=5, description="1–5: the post follows the shared brand policy.")
    hook: Score = Field(ge=1, le=5, description="1–5: the first line gives a reason to keep reading.")


class CriticVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True, populate_by_name=True, title="CriticVerdict")

    pass_: bool = Field(alias="pass", description="The Critic's own overall verdict.")
    scores: CriticScores
    fixes: list[str] = Field(description="Concrete changes for the Writer; at least one when pass is false.")
    unsupported_claims: list[str] = Field(default_factory=list, description="Claims the Critic could not trace to the source.")

    @model_validator(mode="after")
    def _consistent(self) -> CriticVerdict:
        if not self.pass_ and not [f for f in self.fixes if f.strip()]:
            raise ValueError("a failing verdict must carry at least one fix")
        if self.pass_ and self.unsupported_claims:
            raise ValueError("a passing verdict cannot list unsupported claims")
        return self

    @classmethod
    def json_schema(cls) -> dict[str, Any]:
        return cls.model_json_schema(by_alias=True, mode="validation")

    def dump(self) -> dict[str, Any]:
        return self.model_dump(by_alias=True)


_FENCE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def parse_critic(raw: str | dict[str, Any] | Any) -> CriticVerdict:
    """Validate a Critic response. Strings must be one JSON object (a ```json fence is tolerated)."""
    data: Any = raw
    if isinstance(raw, str):
        text = _FENCE.sub("", raw.strip())
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise CriticOutputInvalid(f"Critic output is not JSON: {e.msg} (got {raw[:60]!r})") from e
    if not isinstance(data, dict):
        raise CriticOutputInvalid(f"Critic output must be a JSON object, got {type(data).__name__}")
    try:
        return CriticVerdict.model_validate(data)
    except ValidationError as e:
        first = e.errors()[0]
        where = ".".join(str(x) for x in first.get("loc", ())) or "(root)"
        raise CriticOutputInvalid(f"Critic output failed schema validation at {where}: {first.get('msg')}") from e


class Expect(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    passes: int


class Case(BaseModel):
    """One input to the loop: a source note or a topic, optionally with a draft to start from."""

    model_config = ConfigDict(extra="forbid")

    id: str
    about: str = ""
    note: str | None = None
    topic: str | None = None
    start_draft: str | None = None
    expect: Expect | None = None

    @model_validator(mode="after")
    def _one_input(self) -> Case:
        if bool(self.note) == bool(self.topic):
            raise ValueError("a case has exactly one of `note` or `topic`")
        return self


class Source(BaseModel):
    """What the post must stay faithful to: a build-log note, or the topic text itself."""

    id: str
    title: str
    text: str


Stop = Literal["passed", "cap_hit", "over_budget"]
DraftSource = Literal["written", "supplied", "revised", "unchanged"]


class PassRecord(BaseModel):
    """Everything about one pass: the draft, the Critic's verdict, every G0 result, the decision and the cost."""

    n: int
    draft: str
    draft_source: DraftSource
    critic_valid: bool
    critic: CriticVerdict | None = None
    critic_error: str = ""
    critic_overruled: bool = False
    claims_registry: Literal["clear", "unsupported", "not_checked"] = "not_checked"
    claims_detail: list[dict[str, Any]] = Field(default_factory=list)
    claims_in_source: Literal["pass", "fail", "not_checked"] = "not_checked"
    brand: Literal["pass", "fail", "not_checked"] = "not_checked"
    brand_violations: list[dict[str, Any]] = Field(default_factory=list)
    evaluation_id: str = ""
    evaluation_total: float = 0.0
    criteria: list[dict[str, Any]] = Field(default_factory=list)
    passed: bool = False
    fixes_for_next: list[str] = Field(default_factory=list)
    usage: dict[str, dict[str, Any] | None] = Field(default_factory=dict)


class LoopResult(BaseModel):
    run_id: str
    case_id: str
    source: Source
    cap: int
    passes: list[PassRecord]
    passed: bool
    stop_reason: Stop
    needs_human_review: bool
    final_draft: str
    caller: str
    measured: bool
    tokens: dict[str, int] = Field(default_factory=dict)
    cost_usd: float = 0.0

    def summary(self) -> str:
        n = len(self.passes)
        if self.passed:
            return f"{self.case_id}: passed on pass {n} of {self.cap}."
        if self.stop_reason == "over_budget":
            return f"{self.case_id}: NEEDS HUMAN REVIEW — run cost cap reached after {n} passes (needs human review)."
        return f"{self.case_id}: NEEDS HUMAN REVIEW — cap of {self.cap} hit after {n} passes without a pass (needs human review)."
