"""AC 5: a malformed Critic response is caught by schema validation, not passed through."""

from __future__ import annotations

import json

import jsonschema
import pytest

from post_loop.models import REPO_DIR, CriticOutputInvalid, CriticVerdict, parse_critic

GOOD = {"pass": False, "scores": {"claims": 5, "brand": 4, "hook": 2}, "fixes": ["Sharpen the hook."]}


def test_good_dict_and_json_string_parse():
    v = parse_critic(GOOD)
    assert v.pass_ is False and v.scores.hook == 2 and v.fixes == ["Sharpen the hook."]
    assert parse_critic(json.dumps(GOOD)) == v
    assert parse_critic("```json\n" + json.dumps(GOOD) + "\n```") == v


@pytest.mark.parametrize(
    "raw",
    [
        "Looks good to me! Ship it.",
        "",
        "[1, 2, 3]",
        {"pass": False, "scores": {"claims": 5, "brand": 4}, "fixes": ["x"]},  # missing hook
        {"pass": False, "scores": {"claims": 5, "brand": 4, "hook": 7}, "fixes": ["x"]},  # out of range
        {"pass": False, "scores": {"claims": 0, "brand": 4, "hook": 3}, "fixes": ["x"]},  # out of range
        {"pass": False, "scores": {"claims": 5, "brand": 4, "hook": 3.5}, "fixes": ["x"]},  # not an int
        {"pass": "yes", "scores": {"claims": 5, "brand": 4, "hook": 3}, "fixes": ["x"]},  # not a bool
        {"scores": {"claims": 5, "brand": 4, "hook": 3}, "fixes": ["x"]},  # missing pass
        {"pass": False, "scores": {"claims": 5, "brand": 4, "hook": 3}, "fixes": ["x"], "mood": "happy"},  # extra field
        {"pass": False, "scores": {"claims": 5, "brand": 4, "hook": 3}, "fixes": []},  # a fail with no fixes
        {"pass": True, "scores": {"claims": 5, "brand": 5, "hook": 5}, "fixes": [], "unsupported_claims": ["73%"]},  # contradiction
    ],
)
def test_malformed_is_caught(raw):
    with pytest.raises(CriticOutputInvalid):
        parse_critic(raw)


def test_published_schema_matches_the_model_and_validates_good_output():
    published = json.loads((REPO_DIR / "schemas" / "critic_v1.json").read_text(encoding="utf-8"))
    assert published == CriticVerdict.json_schema()
    jsonschema.validate(GOOD, published)
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate({"pass": True}, published)
