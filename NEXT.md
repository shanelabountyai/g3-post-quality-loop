# NEXT

## 2026-11-24 — Pre-live portfolio pack (branch `portfolio-pack/2026-11-24`, draft PR, docs only)

**State:** `main` = `a51a5ab` (PR #1 merged 2026-11-20 CT). **Not deployed. No live model call has ever been made.** This pack adds docs only; no code, test, fixture, recording, rubric, schema, brand policy, config, CI or generated report changed. Decisions D-18 to D-23 added. The 2026-11-21 section below is kept as written; its "nothing is merged" line is now out of date (PR #1 is merged).

**Done:**
- Gate re-run, same steps as CI → `docs/GATE-2026-11-24.md`.
- `docs/DEMO.md` — At a glance block plus a 10-stop recorded-path walk-through.
- Exec brief, private Claude Docs: [G3·C Post Quality Loop in Brief](https://claude.ai/artifact/CFfJ1t9Asd8MV9evAEAbPr) (not shared).
- `docs/COST.md` — measured figures only (D-21).
- `docs/LINKEDIN_DRAFTS.md` — two drafts on D-10 and D-12, "Drafted, unposted".
- `docs/RELEASE_NOTES.md` — "Not deployed — portfolio pack 2026-11-24".

**Verified, and how (2026-11-24, fresh sandbox, recorded path, no `--live`):**
- `uv sync --frozen` exit 0 · `uv run ruff check .` exit 0, all checks passed · `uv run mypy` exit 0, no issues in 10 source files · `uv run pytest` exit 0, 79 passed · `post-loop eval` as `ci.yml` runs it, exit 0: 9 cases, avg passes to pass 2.14, cap-hit rate 2 of 9 (**hand-written recorded responses, not a model**); report body identical to the committed `docs/eval-report.md`.
- DEMO stops 1–9 run as commands (exit codes 0, 0, 0, 1, 2, 2, 0, 0 as documented) and tied to named tests.
- Both LinkedIn drafts pass the loop's own brand gate (G0 v1 + `g3-skill-1`), checked with a script kept outside the repo (D-22).
- Every build commit listed in the release notes is on `main` (`git merge-base --is-ancestor`).

**Not verified:**
- Any live model run, real tokens, cost per post, passes-to-pass or cap-hit rate.
- Build cost (not recorded anywhere).
- G0's price table against Anthropic's pricing page.
- DEMO stop 10 (live run); the `--live` refusal was checked by tests only, not from the command line.
- Whether the drafts sound like you; whether the brief reads right to a hiring lead.

**Doc fixes that would need a code change:** none found.

**You:**
1. Review the draft PR for `portfolio-pack/2026-11-24`; it is on hold until you do. Merge it yourself if you're happy.
2. Walk through `docs/DEMO.md` stops 1–9 on your machine.
3. Read the brief (link above) and decide whether to share it.
4. Edit the two drafts in `docs/LINKEDIN_DRAFTS.md` into your own words before posting anything.
5. When you want real numbers, do the one live run (2026-11-21 "You:" step 3 below), then update `docs/COST.md` and the brief with what it measured.

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
