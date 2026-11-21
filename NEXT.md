# NEXT

State (2026-11-04): PRD only (`docs/prd.md`, v0.1). No code, no git repo yet.

Next: owner creates the repo if wanted, then pastes `KICKOFF.md` into Claude Code. The session plans first and stops for review.

Order: G1 -> G0 (shared layer) -> G2 -> G3 -> G4 -> G5 (see ../README.md). If G0 isn't built when this starts, use stubs with the same contract shape.

## 2026-11-21 — G3·C built unattended (branch `build/g3c`, draft PR)

**State:** G3·C (Python + Claude Agent SDK) is built end to end on the recorded/fake model path, attached to G0 at `6f5e605`. G3·B (n8n) was not built (D-1; owner's hand build). Nothing is merged; nothing is posted; no API key was used and no model was called.

**What was built** (backlog C1–C9, `docs/BACKLOG.md`): `post-loop "topic"` / `--note` / `--case`; the Writer → Critic → G0 gate loop with a hard cap of 3; the Critic schema with validation (`schemas/critic_v1.json`); G0 adapter seeding rubric `g3_linkedin_post_v1` and brand policy `g3-skill-1`; draft-file-only output under `out/`; `post-loop eval` report (`docs/eval-report.md`); CI workflow (lint, typecheck, tests, eval).

**Gate (fresh clone of `build/g3c`, 2026-11-21):** `uv sync --frozen` ok · `ruff check .` all checks passed · `mypy` no issues in 10 source files · `pytest` 79 passed · `post-loop eval` 9 cases, 7 passed, 2 needs human review, **avg passes to pass 2.14, cap-hit rate 22%**, 2 malformed Critic outputs caught, 1 Critic pass overruled by G0, 0 tokens / $0 (recorded fixtures — these numbers describe hand-written fixtures, not a model).

**Provisional decisions for Shane** (taken from the PRD's recommendations; see `docs/DECISIONS.md`):
- D-2 pass cap 3.
- D-3 Writer and Critic on the same model (`claude-sonnet-5-5`).
- D-4 brand rules seeded from your `linkedin-personal-brand-shane` skill as G0 policy version `g3-skill-1` (checked alongside G0 v1). Employer, career-record and job-search guardrails were deliberately **not** copied into this public repo.
- D-5 passing drafts stay as drafts; no post-ledger writes.

**Not verified:**
- No live model call: `AgentSdkCaller` is implemented but has never run; real tokens, cost per post, passes-to-pass and cap-hit rate are unmeasured.
- Model ids and prices are G0's table (G1 D-35 says confirmed on Anthropic's pricing page); not re-checked in this run.
- The hand-written recordings are designed outcomes; a real Critic may score differently.
- The G3 seeds go into G0's store through G0's loader, not a tool (same exception as G2 D-2/D-25).

**You:**
1. Review the draft PR and the four provisional decisions (D-2..D-5); say which to change.
2. Check `brand/brand_policy_g3_skill_1.json` against your skill — add or cut rules you want enforced.
3. When you want real numbers: put `ANTHROPIC_API_KEY` in a gitignored `.env`, export it, and run `uv run post-loop --note g3-post-loop --live` once (≈ 6 model calls at most; G0's $10 run cap applies). Then `uv run post-loop eval --live --report docs/eval-report-live.md` runs all 9 fixture inputs live (at most 27 Critic + 27 Writer calls) and gives the first measured passes-to-pass and cap-hit rate; the `expect` outcomes in `fixtures/cases.json` only apply to the recorded path.
4. Merge the PR yourself when satisfied (no one else will), then tag G0 `v0.1.0` if you want the pin moved off the SHA.
5. Build G3·B in n8n by hand from `docs/prd.md` and the same rubric/fixtures.
