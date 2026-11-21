"""Nothing is posted anywhere. Output is a draft file only."""

from __future__ import annotations

import ast
import json

import pytest

from post_loop.fixtures import load_cases
from post_loop.llm import RecordedCaller
from post_loop.loop import PostLoop
from post_loop.models import REPO_DIR
from post_loop.output import OutputError, write_result

NETWORK_MODULES = {"requests", "httpx", "urllib", "urllib3", "http", "aiohttp", "socket", "smtplib", "googleapiclient"}


def test_package_imports_no_network_client():
    for path in (REPO_DIR / "src" / "post_loop").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                names = [node.module]
            for n in names:
                assert n.split(".")[0] not in NETWORK_MODULES, f"{path.name} imports {n}"


def test_the_only_sink_writes_draft_files_under_out(layer, tmp_path):
    cases = load_cases()
    r = PostLoop(layer=layer, caller=RecordedCaller(), cap=3, run_id="t").run(cases.by_id("weak-draft-cap"))
    paths = write_result(r, out_dir=tmp_path / "out")
    assert {p.suffix for p in paths} == {".md", ".json"}
    assert all(tmp_path / "out" in p.parents for p in paths)
    md = paths[0].read_text(encoding="utf-8")
    assert md.startswith("---\n") and "status: needs_human_review" in md and "posted: false" in md
    log = json.loads(paths[1].read_text(encoding="utf-8"))
    assert log["needs_human_review"] is True and len(log["passes"]) == 3


def test_sink_refuses_path_escape(layer, tmp_path):
    cases = load_cases()
    r = PostLoop(layer=layer, caller=RecordedCaller(), cap=3, run_id="../escape").run(cases.by_id("g0-pass-first"))
    with pytest.raises(OutputError):
        write_result(r, out_dir=tmp_path / "out")


def test_prompts_carry_pointers_not_copied_rules():
    from post_loop import prompts

    text = prompts.WRITER.system_prompt() + prompts.CRITIC.system_prompt()
    brand = json.loads((REPO_DIR / "brand" / "brand_policy_g3_skill_1.json").read_text(encoding="utf-8"))
    for rule in brand["rules"]:
        if rule["kind"] == "phrase":
            assert rule["pattern"].lower() not in text.lower()
    for phrase in ("excited to share", "game-changer", "synergy", "circle back", "pick your brain"):
        assert phrase not in text.lower()
    assert "4,5" not in text and "pass_threshold" not in text


def test_live_caller_refuses_without_a_key():
    from post_loop.llm import AgentSdkCaller, LiveCallRefused

    with pytest.raises(LiveCallRefused):
        AgentSdkCaller()
