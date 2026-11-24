# Release notes — G3·C Post Quality Loop

## Not deployed — portfolio pack 2026-11-24

**Not deployed. No live model call has been made.** This is a closeout pack without live verification. Every eval number in this repo comes from hand-written recorded model responses (`fixtures/recorded.json`, D-9), not from a model.

### What exists (on `main`, each commit checked with `git merge-base --is-ancestor <sha> main` on 2026-11-24)

| Commit | What |
|---|---|
| `a51a5ab` | Merge of PR #1, "G3·C Post Quality Loop: full build (recorded model)", merged 2026-11-20 (CT). CI run 5 on this commit: success. |
| `f1cc80b` | Kickoff kit: `CLAUDE.md`, `KICKOFF.md`, `NEXT.md`, `docs/prd.md` (D-17). |
| `182d8ca` | Plan, decisions, rubric and brand seeds, fixtures, failing tests first (backlog C1, C3 tests). |
| `9bb1a52` | The build: G0 adapter, Critic schema, recorded caller, loop, draft-file sink, CLI, report (C2–C8). |
| `0adf539` | README. |
| `26ab1cc`, `ef0b674` | NEXT.md hand-off section and a correction to its live-eval step. |
| `8691d18` | CI fix: no job-level runner context; `G0_DB_PATH` set in the eval step. |

In short: `post-loop "topic"` / `--note` / `--case` run a Writer → Critic → G0-gate loop with a hard cap of 3; a cap hit writes `status: needs_human_review` and exits 2; `post-loop eval` writes the report. 79 tests. Nothing posts anywhere.

### The pack (branch `portfolio-pack/2026-11-24`, docs only)

| Item | Where | State |
|---|---|---|
| Gate re-run (CI steps, recorded path) | `docs/GATE-2026-11-24.md` | Done: all 5 steps exit 0; 79 passed; eval report reproduces |
| Demo walk-through | `docs/DEMO.md` | Done: 9 of 10 stops verified in this session; stop 10 (live run) not run; Shane has not walked it |
| Exec brief | Claude Docs, private: [G3·C Post Quality Loop in Brief](https://claude.ai/artifact/CFfJ1t9Asd8MV9evAEAbPr) | Drafted; not shared |
| Cost note | `docs/COST.md` | Done: build and per-post cost not measured; limits quoted with sources |
| LinkedIn drafts | [`docs/LINKEDIN_DRAFTS.md`](LINKEDIN_DRAFTS.md) | Drafted, unposted (2) |
| Release notes | `docs/RELEASE_NOTES.md` | This entry |
| Hand-off | `NEXT.md`, section 2026-11-24 | Done |
| Decisions | `docs/DECISIONS.md` D-18 to D-23 | Added; no existing row edited |

### Not verified

- Any live model behaviour, cost, tokens, passes-to-pass or cap-hit rate.
- The G0 price table against Anthropic's current pricing page.
- The demo, brief and drafts by Shane.
