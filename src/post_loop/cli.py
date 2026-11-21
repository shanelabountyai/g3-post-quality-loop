"""`post-loop "topic"` — run the loop; `post-loop eval` — run every fixture case and write the report.

Exit codes: 0 passed · 2 needs human review (cap hit) · 1 error.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import UTC, datetime
from pathlib import Path

from post_loop.fixtures import load_cases
from post_loop.layer import Layer, LayerDegraded
from post_loop.llm import AgentSdkCaller, LiveCallRefused, ModelCaller, RecordedCaller
from post_loop.loop import MAX_CAP_DEFAULT, PostLoopError, run_case
from post_loop.models import REPO_DIR, Case, LoopResult
from post_loop.output import DEFAULT_OUT, OutputError, write_result
from post_loop.report import build_report, summarize


def _err(msg: str) -> int:
    print(f"post-loop: {msg}", file=sys.stderr)
    return 1


def _caller(live: bool) -> ModelCaller:
    return AgentSdkCaller() if live else RecordedCaller()


def _common(p: argparse.ArgumentParser) -> None:
    p.add_argument("--cap", type=int, default=MAX_CAP_DEFAULT, help="pass cap (default 3, D-2)")
    p.add_argument("--allow-cap-above-3", action="store_true", help="permit --cap above 3 (costs more per post)")
    p.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output directory for draft files (default out/)")
    p.add_argument("--run-id", default=None, help="run id (default: UTC timestamp)")
    p.add_argument("--db", default=None, help="G0 SQLite file (default: G0_DB_PATH or ~/.g0-shared-layer/layer.sqlite)")
    p.add_argument("--live", action="store_true", help="call Claude via the Agent SDK (needs ANTHROPIC_API_KEY; not used in this build)")


def _check_cap(args: argparse.Namespace) -> str | None:
    if args.cap < 1:
        return "--cap must be at least 1"
    if args.cap > MAX_CAP_DEFAULT and not args.allow_cap_above_3:
        return f"--cap {args.cap} is above the provisional cap of {MAX_CAP_DEFAULT} (D-2); add --allow-cap-above-3 to permit it"
    return None


def _print_result(r: LoopResult) -> None:
    for p in r.passes:
        if p.critic:
            s = p.critic.scores
            print(f"  pass {p.n} [{p.draft_source}] claims={s.claims} brand={s.brand} hook={s.hook} · G0 claims={p.claims_registry}/"
                  f"{p.claims_in_source} brand={p.brand} total={p.evaluation_total:.2f} → {'PASS' if p.passed else 'fail'}"
                  + (" (Critic pass overruled by G0)" if p.critic_overruled else ""))
        else:
            print(f"  pass {p.n} [{p.draft_source}] Critic output INVALID → fail ({p.critic_error})")
    print(r.summary())


def run_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="post-loop", description="Writer + Critic loop with a hard pass cap. Output is a draft file only.")
    p.add_argument("topic", nargs="?", help="topic to write about")
    p.add_argument("--case", help="run one fixture case by id")
    p.add_argument("--note", help="run on a fixture source note by id")
    _common(p)
    args = p.parse_args(argv)
    if (msg := _check_cap(args)):
        return _err(msg)
    cases = load_cases()
    case: Case | None
    if args.case:
        try:
            case = cases.by_id(args.case)
        except KeyError as e:
            return _err(str(e))
    elif args.note:
        if args.note not in cases.notes:
            return _err(f"no note '{args.note}'. Known: {sorted(cases.notes)}")
        case = next((c for c in cases.cases if c.note == args.note and not c.start_draft), None) or Case(id=f"note-{args.note}", note=args.note)
    elif args.topic:
        case = cases.by_topic(args.topic) or Case(id="topic", topic=args.topic)
    else:
        return _err("give a topic, --case or --note")
    try:
        caller = _caller(args.live)
    except LiveCallRefused as e:
        return _err(str(e))
    if isinstance(caller, RecordedCaller) and not caller.has(f"critic:{case.id}:1"):
        return _err(f"no recording for {case.id!r} on the recorded path; known topics/cases are in fixtures/cases.json. "
                    "A new topic needs --live with ANTHROPIC_API_KEY (D-9).")
    run_id = args.run_id or datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    try:
        layer = Layer(db_path=args.db)
    except LayerDegraded as e:
        return _err(str(e))
    try:
        r = run_case(layer, caller, case, run_id=run_id, cap=args.cap, cases=cases)
        paths = write_result(r, out_dir=args.out)
    except (PostLoopError, LayerDegraded, OutputError) as e:
        return _err(str(e))
    finally:
        layer.close()
    _print_result(r)
    print(f"draft: {paths[0]}\npasses log: {paths[1]}")
    return 0 if r.passed else 2


def eval_main(argv: list[str]) -> int:
    p = argparse.ArgumentParser(prog="post-loop eval", description="Run every fixture case; report passes-to-pass and cap-hit rate.")
    _common(p)
    p.add_argument("--report", type=Path, default=REPO_DIR / "docs" / "eval-report.md")
    p.add_argument("--json", type=Path, default=None, help="also write the summary numbers as JSON")
    args = p.parse_args(argv)
    if (msg := _check_cap(args)):
        return _err(msg)
    try:
        caller = _caller(args.live)
    except LiveCallRefused as e:
        return _err(str(e))
    run_id = args.run_id or "eval-" + datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")
    cases = load_cases()
    try:
        layer = Layer(db_path=args.db)
    except LayerDegraded as e:
        return _err(str(e))
    results: list[LoopResult] = []
    try:
        for c in cases.cases:
            r = run_case(layer, caller, c, run_id=run_id, cap=args.cap, cases=cases)
            write_result(r, out_dir=args.out)
            results.append(r)
            _print_result(r)
    except (PostLoopError, LayerDegraded, OutputError) as e:
        return _err(str(e))
    finally:
        layer.close()
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(build_report(results, run_id=run_id, cap=args.cap), encoding="utf-8")
    s = summarize(results)
    if args.json:
        args.json.write_text(json.dumps(s, indent=2) + "\n", encoding="utf-8")
    print(f"\navg passes to pass: {s['avg_passes_to_pass']} · cap-hit rate: {s['cap_hit_rate']} · report: {args.report}")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if argv[:1] == ["eval"]:
        return eval_main(argv[1:])
    return run_main(argv)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
