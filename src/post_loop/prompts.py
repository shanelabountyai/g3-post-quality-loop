"""Writer and Critic specs (D-3).

The prompts carry one-line pointers to the shared layer, never the rules themselves: the never-use list and the
brand voice live in G0 `brand.policy` (v1 + g3-skill-1), the numbers rule in G0 `claims.registry` and rubric
`claim_rule_v1`, the pass thresholds in rubric `g3_linkedin_post_v1`. Whatever the model does, the loop re-checks
every draft against those in code (D-8, D-10). `tests/test_safety.py` pins that no rule text leaks in here.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

from post_loop.models import CriticVerdict

MODEL = "claude-sonnet-5-5"  # same model for both (D-3, provisional)

WRITER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "additionalProperties": False,
    "required": ["post"],
    "properties": {"post": {"type": "string", "minLength": 1, "description": "The full LinkedIn post, hashtags last."}},
}


@dataclass(frozen=True)
class AgentSpec:
    name: str
    model: str
    instructions: str
    schema: dict[str, Any]
    max_turns: int = 1

    def system_prompt(self) -> str:
        return self.instructions


WRITER = AgentSpec(
    name="writer",
    model=MODEL,
    schema=WRITER_SCHEMA,
    instructions=(
        "You are the Writer. Draft one LinkedIn post for Shane LaBounty from the SOURCE given, or revise the DRAFT "
        "using the FIXES given. Use only facts in the SOURCE; do not add numbers, names or results it does not contain. "
        "Brand voice, claims and the hook are checked after you by the shared layer (brand.policy, claims.registry, "
        "evaluation); follow its fixes exactly. Return JSON: {\"post\": \"...\"}."
    ),
)

CRITIC = AgentSpec(
    name="critic",
    model=MODEL,
    schema=CriticVerdict.json_schema(),
    instructions=(
        "You are the Critic. Score the DRAFT against the SOURCE on three criteria, each an integer from 1 to 5: "
        "claims (every factual claim is in the SOURCE), brand (Shane's brand voice), hook (does the first line give a "
        "reason to keep reading). List every claim you cannot trace to the SOURCE in unsupported_claims. Set pass only "
        "if you would publish it as is; if not, give concrete fixes. Your verdict is re-checked by the shared layer. "
        "Return JSON only, matching the schema."
    ),
)


def writer_input(source_title: str, source_text: str, draft: str | None = None, fixes: list[str] | None = None) -> str:
    payload: dict[str, Any] = {"SOURCE": {"title": source_title, "text": source_text}}
    if draft is not None:
        payload["DRAFT"] = draft
        payload["FIXES"] = fixes or []
    return json.dumps(payload, ensure_ascii=False)


def critic_input(source_title: str, source_text: str, draft: str) -> str:
    return json.dumps({"SOURCE": {"title": source_title, "text": source_text}, "DRAFT": draft}, ensure_ascii=False)
