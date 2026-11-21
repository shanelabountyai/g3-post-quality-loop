"""AC 1–4 on the recorded fixtures, plus the cap for every cap value."""

from __future__ import annotations

import pytest

from post_loop.fixtures import load_cases
from post_loop.layer import LayerDegraded
from post_loop.llm import RecordedCaller
from post_loop.loop import PostLoop, PostLoopError

CASES = load_cases()


def _run(layer, case_id, cap=3, caller=None):
    loop = PostLoop(layer=layer, caller=caller or RecordedCaller(), cap=cap, run_id="t")
    return loop.run(CASES.by_id(case_id))


@pytest.mark.parametrize("case", CASES.cases, ids=lambda c: c.id)
def test_every_case_matches_its_expected_outcome(layer, case):
    r = _run(layer, case.id)
    assert r.passed is case.expect.passed
    assert len(r.passes) == case.expect.passes
    assert r.needs_human_review is (not case.expect.passed)
    assert r.stop_reason == ("passed" if case.expect.passed else "cap_hit")


def test_ac1_weak_draft_improves_with_scores_logged(layer):
    r = _run(layer, "weak-draft-improves")
    hooks = [p.critic.scores.hook for p in r.passes]
    brands = [p.critic.scores.brand for p in r.passes]
    totals = [p.evaluation_total for p in r.passes]
    assert hooks == sorted(hooks) and hooks[-1] > hooks[0]
    assert brands[-1] > brands[0]
    assert totals == sorted(totals) and totals[-1] > totals[0]
    assert r.passed and r.passes[-1].passed
    # every pass carries its scores, the G0 results and the fixes that drove the next revision
    for p in r.passes:
        assert p.critic is not None and p.evaluation_id and p.criteria
    assert r.passes[0].draft_source == "supplied" and r.passes[1].draft_source == "revised"


@pytest.mark.parametrize("cap", [1, 2, 3])
@pytest.mark.parametrize("case", CASES.cases, ids=lambda c: c.id)
def test_ac2_never_exceeds_the_cap(layer, case, cap):
    caller = RecordedCaller()
    r = _run(layer, case.id, cap=cap, caller=caller)
    assert 1 <= len(r.passes) <= cap
    assert caller.calls["critic"] == len(r.passes)
    assert caller.calls["writer"] <= cap
    if len(r.passes) == cap and not r.passed:
        assert r.needs_human_review


def test_ac2_cap_must_be_positive(layer):
    with pytest.raises(PostLoopError):
        PostLoop(layer=layer, caller=RecordedCaller(), cap=0, run_id="t")


def test_ac3_unsupported_claim_never_passes_even_when_critic_says_pass(layer):
    r = _run(layer, "unsupported-claim")
    assert not r.passed
    assert all(not p.passed for p in r.passes)
    assert all(p.claims_registry == "unsupported" or p.claims_in_source == "fail" for p in r.passes)
    overruled = [p for p in r.passes if p.critic_overruled]
    assert overruled and overruled[0].critic.pass_ is True
    assert any(c["status"] == "unsupported" for p in r.passes for c in p.claims_detail)


def test_ac3_any_unsupported_number_fails_even_if_the_rest_is_perfect(layer):
    from post_loop.loop import gate

    note = CASES.note("g0-shared-layer")
    draft = CASES.recorded("writer:g0-pass-first:1")["post"] + "\n\nIt also cut costs by 41%."
    critic = CASES.critic_ok()
    g = gate(layer, draft=draft, source=note, critic=critic, run_id="t")
    assert g.claims_in_source == "fail" and not g.passed


def test_ac4_cap_hit_is_flagged_not_silent(layer, tmp_path):
    r = _run(layer, "weak-draft-cap")
    assert r.stop_reason == "cap_hit" and r.needs_human_review and not r.passed
    assert "needs human review" in r.summary().lower()


def test_ac5_malformed_critic_is_caught_and_fails_closed(layer):
    r = _run(layer, "malformed-critic")
    p1, p2, p3 = r.passes
    assert not p1.critic_valid and not p1.passed and "not JSON" in p1.critic_error
    assert not p2.critic_valid and not p2.passed and p2.critic_error
    assert p3.critic_valid and p3.passed
    # no revision without trustworthy fixes: the same draft is re-critiqued
    assert p1.draft == p2.draft == p3.draft
    assert [p.draft_source for p in r.passes] == ["written", "unchanged", "unchanged"]


def test_malformed_on_last_pass_ends_in_review(layer):
    r = _run(layer, "malformed-critic", cap=2)
    assert not r.passed and r.needs_human_review


def test_every_call_is_logged_to_g0_observability(layer):
    caller = RecordedCaller()
    r = _run(layer, "g3-third-pass", caller=caller)
    total = layer.run_total("t")
    assert total.calls == caller.calls["writer"] + caller.calls["critic"] == 6
    assert total.cost_usd == 0.0  # recorded path: not measured live
    assert all(p.usage["writer"] is not None for p in r.passes)


def test_finished_event_recorded_in_g0_measurement(layer):
    _run(layer, "g0-pass-first")
    rows = layer.db.conn.execute("SELECT event FROM events WHERE run_id = 't'").fetchall()
    assert [r[0] for r in rows] == ["post_loop.finished"]


def test_degraded_layer_stops_before_any_model_call(layer):
    with layer.db.conn:
        layer.db.conn.execute("DELETE FROM rubrics WHERE id = 'g3_linkedin_post_v1'")
    caller = RecordedCaller()
    with pytest.raises(LayerDegraded):
        _run(layer, "g0-pass-first", caller=caller)
    assert sum(caller.calls.values()) == 0
