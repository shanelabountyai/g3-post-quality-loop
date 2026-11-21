# Backlog — G3·C Post Quality Loop (code version)

G3·B (n8n) is out of scope for this build (D-1); the owner builds it by hand. Each task is one sitting, test-first where practical. Acceptance criteria (AC) are the PRD's.

| # | Task | Acceptance | Status |
|---|---|---|---|
| C1 | Project skeleton: `pyproject.toml` (Python 3.12, uv), G0 pinned by SHA, `post-loop` console script, ruff + mypy + pytest, CI workflow. | `uv sync --frozen`, `ruff check`, `mypy src`, `pytest` all run. | done |
| C2 | G0 adapter (`layer.py`): health first, seed `g3_linkedin_post_v1` + brand policy `g3-skill-1` through G0's loader (namespaced only), claims, brand, evaluate, observability, measurement. | Health refuses a degraded layer; loader refuses non-`g3` ids; the G0 v1 policy and rubrics are untouched. | done |
| C3 | Critic schema (`models.CriticVerdict`) + `parse_critic`; publish `schemas/critic_v1.json`. | **AC 5**: non-JSON, missing field, out-of-range score, extra field, `pass:false` with no fixes, `pass:true` with unsupported claims → `CriticOutputInvalid`. | done |
| C4 | Writer/Critic specs (`prompts.py`) with one-line pointers to G0, no copied rules; `RecordedCaller` + `AgentSdkCaller` (`llm.py`). | Prompts contain no never-use list or rubric text (test); recorded caller makes no network call; live caller refuses without a key. | done |
| C5 | The loop (`loop.py`): draft → critique → G0 gate → revise, stop on pass or cap, every pass logged (scores, G0 results, fixes, tokens, cost). | **AC 1** weak draft's scores rise across passes; **AC 2** passes ≤ cap for every case and cap values; **AC 3** unsupported claim never passes, even with a Critic false positive; **AC 4** cap → `needs_human_review`. | done |
| C6 | Output sink (`output.py`): draft file + passes log under `out/` only. | Path escape refused; no network/ledger sink exists in the package (test scans imports). | done |
| C7 | CLI `post-loop "topic"` / `--case` / `--note`, exit codes (0 passed, 2 needs review, 1 error); `post-loop eval`. | CLI tests via `main(argv)`. | done |
| C8 | Report (`report.py`): average passes-to-pass, cap-hit rate, per-case trace → `docs/eval-report.md`. | Numbers recomputed in a test from the fixtures' expected outcomes. | done |
| C9 | Hand-off: README, NEXT.md dated section, PR. | Gate results recorded verbatim. | done |

## Later (not in this build)

- First live run with a key (`post-loop --live --record …`) to replace the hand-made recordings and get real tokens/cost per post.
- Different-model Critic as a measured comparison (PRD decision 2, second half).
- G0 `rubric.register` tool so G2/G3 stop seeding through the loader (G2 D-25).
- G3·B in n8n (owner, by hand).

## Owner hand steps

See NEXT.md, section 2026-11-21 ("You:" steps).
