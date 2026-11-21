"""The only sink (C6, D-5): a draft file and a passes log under `out/<run_id>/`. Nothing is posted anywhere."""

from __future__ import annotations

import json
from pathlib import Path

from post_loop.models import LoopResult

DEFAULT_OUT = Path("out")


class OutputError(RuntimeError):
    """Refused to write outside the output directory."""


def _inside(base: Path, target: Path) -> bool:
    try:
        target.resolve().relative_to(base.resolve())
        return True
    except ValueError:
        return False


def write_result(result: LoopResult, out_dir: Path | None = None) -> list[Path]:
    base = (out_dir or DEFAULT_OUT)
    run_dir = base / result.run_id
    md_path, log_path = run_dir / f"{result.case_id}.md", run_dir / f"{result.case_id}.passes.json"
    for p in (run_dir, md_path, log_path):
        if not _inside(base, p) or ".." in Path(result.run_id).parts or ".." in Path(result.case_id).parts:
            raise OutputError(f"refusing to write outside {base}: {p}")
    run_dir.mkdir(parents=True, exist_ok=True)

    status = "passed" if result.passed else "needs_human_review"
    last = result.passes[-1] if result.passes else None
    lines = [
        "---",
        f"case: {result.case_id}",
        f"source: {result.source.id}",
        f"status: {status}",
        f"stop_reason: {result.stop_reason}",
        f"passes: {len(result.passes)}",
        f"cap: {result.cap}",
        f"caller: {result.caller}",
        f"measured_live: {str(result.measured).lower()}",
        "posted: false",
        "---",
        "",
    ]
    if not result.passed:
        lines += ["> **Needs human review.** The loop stopped without a passing draft. Last pass's open fixes:", ">"]
        for f in (last.fixes_for_next if last and last.fixes_for_next else [last.critic_error if last else "no pass ran"]):
            lines.append(f"> - {f}")
        lines.append("")
    lines += [result.final_draft, ""]
    md_path.write_text("\n".join(lines), encoding="utf-8")
    log_path.write_text(json.dumps(result.model_dump(mode="json", by_alias=True), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return [md_path, log_path]
