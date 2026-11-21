from __future__ import annotations

import json

from post_loop.cli import main
from post_loop.fixtures import load_cases
from post_loop.report import summarize


def test_cli_topic_runs_recorded(tmp_path, capsys):
    code = main(["What a hard pass cap teaches an agent", "--out", str(tmp_path), "--run-id", "r1"])
    out = capsys.readouterr().out
    assert code == 0 and "passed on pass 1" in out
    assert (tmp_path / "r1" / "topic-pass-cap.md").exists()


def test_cli_cap_hit_exit_code_2(tmp_path, capsys):
    code = main(["--case", "weak-draft-cap", "--out", str(tmp_path), "--run-id", "r2"])
    assert code == 2 and "NEEDS HUMAN REVIEW" in capsys.readouterr().out


def test_cli_unknown_topic_is_a_clear_error(tmp_path, capsys):
    code = main(["Something with no recording", "--out", str(tmp_path)])
    assert code == 1 and "no recording" in capsys.readouterr().err.lower()


def test_cli_refuses_cap_above_3_without_flag(tmp_path, capsys):
    assert main(["--case", "g0-pass-first", "--cap", "5", "--out", str(tmp_path)]) == 1


def test_cli_live_refused_without_key(tmp_path, capsys):
    assert main(["--case", "g0-pass-first", "--live", "--out", str(tmp_path)]) == 1
    assert "ANTHROPIC_API_KEY" in capsys.readouterr().err


def test_eval_report_numbers(tmp_path, capsys):
    report = tmp_path / "eval.md"
    code = main(["eval", "--out", str(tmp_path / "o"), "--report", str(report), "--json", str(tmp_path / "eval.json")])
    assert code == 0
    data = json.loads((tmp_path / "eval.json").read_text())
    cases = load_cases().cases
    passed = [c for c in cases if c.expect.passed]
    assert data["cases"] == len(cases)
    assert data["passed"] == len(passed)
    assert data["avg_passes_to_pass"] == round(sum(c.expect.passes for c in passed) / len(passed), 2)
    assert data["cap_hit_rate"] == round((len(cases) - len(passed)) / len(cases), 4)
    assert data["max_passes"] <= 3
    assert data["malformed_caught"] == 2 and data["critic_overruled"] >= 1
    md = report.read_text()
    assert "Average passes to pass" in md and "Cap-hit rate" in md and "not measured live" in md


def test_summarize_handles_no_passes():
    assert summarize([])["avg_passes_to_pass"] is None
