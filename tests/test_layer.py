from __future__ import annotations

import json

import pytest

from post_loop.layer import BRAND_POLICY_VERSION, RUBRIC_ID, Layer, LayerDegraded


def test_health_first_and_seeds_present(layer):
    h = layer.require_healthy()
    assert h.status == "ok"
    assert RUBRIC_ID in h.rubrics
    assert BRAND_POLICY_VERSION in h.policy_versions and "1" in h.policy_versions
    # G0's own seeds are untouched
    assert {"post_angle_v1", "claim_rule_v1", "digest_item_v1"} <= set(h.rubrics)


def test_seeding_is_idempotent(tmp_path):
    p = str(tmp_path / "l.sqlite")
    a = Layer(db_path=p)
    n1 = a.health().seeds
    a.close()
    b = Layer(db_path=p)
    assert b.health().seeds == n1
    b.close()


def test_loader_refuses_non_namespaced_rubric(tmp_path):
    bad = tmp_path / "rubric.json"
    bad.write_text(json.dumps({"rubrics": [{"id": "post_angle_v1", "title": "x", "source": "x", "pass_threshold": 1, "criteria": []}]}))
    with pytest.raises(LayerDegraded):
        Layer(db_path=str(tmp_path / "l.sqlite"), rubric_file=bad)


def test_loader_refuses_non_namespaced_brand_rules(tmp_path):
    bad = tmp_path / "brand.json"
    bad.write_text(json.dumps({"policy_version": "1", "source": "x", "text": "x", "channels": ["linkedin"],
                               "rules": [{"id": "never_use.synergy", "kind": "phrase", "pattern": "x", "channels": ["*"], "severity": "fail", "fix": "x"}]}))
    with pytest.raises(LayerDegraded):
        Layer(db_path=str(tmp_path / "l.sqlite"), brand_file=bad)


def test_g0_v1_policy_still_enforced_and_skill_policy_adds_rules(layer):
    v1 = layer.check_brand("Excited to share this", policy_version="1")
    assert not v1.passed
    # 'I've been thinking a lot about' is not in G0 v1 but is in the skill-seeded version
    t = "I've been thinking a lot about intake forms."
    assert layer.check_brand(t, policy_version="1").passed
    skill = layer.check_brand(t, policy_version=BRAND_POLICY_VERSION)
    assert not skill.passed and skill.violations[0].rule_id == "g3.opener.been_thinking_a_lot"


def test_brand_gate_requires_both_versions(layer):
    ok, violations = layer.brand_gate("With 20+ years in marketing, I know.")
    assert not ok and any(v.rule_id == "g3.tenure.years_plus" for v in violations)
    ok, violations = layer.brand_gate("A synergy story.")
    assert not ok and any(v.rule_id == "never_use.synergy" for v in violations)
    ok, violations = layer.brand_gate("A plain sentence about intake.")
    assert ok and violations == []


def test_degraded_rubric_missing_stops(layer):
    with layer.db.conn:
        layer.db.conn.execute("DELETE FROM rubrics WHERE id = ?", (RUBRIC_ID,))
    with pytest.raises(LayerDegraded):
        layer.require_healthy()
