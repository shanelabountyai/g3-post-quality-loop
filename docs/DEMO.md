# Demo — G3·C Post Quality Loop (recorded path)

**Not deployed. No live model call has ever been made.** Every run below replays hand-written recorded model responses (`fixtures/recorded.json`, D-9). The scores and counts you see describe those fixtures, not a model.

## At a glance

- **Who it is for.** Someone who turns build-log write-ups into LinkedIn posts and wants each draft checked before a person reads it: are the claims in the source, is it on-brand, does the first line earn the second. In this repo that person is the owner; the loop is also a worked example of an evaluator–optimizer agent with a hard stop.
- **What was decided.** Hard cap of 3 passes (D-2). Writer and Critic on the same model (D-3). Brand rules seeded from the owner's personal-brand skill as a separate policy version checked alongside the shared one, with personal guardrails kept out of this public repo (D-4). Passing drafts stay drafts; nothing is posted (D-5). A draft passes only if the Critic **and** the shared layer agree (D-10). A malformed Critic answer fails closed and uses up its pass (D-12). Hitting the cap says "needs human review" and exits 2 (D-13).
- **What was left out.** The n8n version, G3·B (D-1; the owner builds it by hand). Any live model call (D-9). Posting, or writing to a post ledger (D-5). A different-model Critic comparison and a `rubric.register` tool in the shared layer (BACKLOG "Later").
- **The complete journey.** Pick a source (a topic, a build-log note, or a supplied draft) → the shared layer's health check runs first → up to 3 passes of Writer → Critic → shared-layer gate → stop on a pass, or at the cap with "needs human review" → a draft file plus a log of every pass under `out/` → `post-loop eval` rolls all cases into a report (average passes to pass, cap-hit rate).
- **Why someone would come back in week three.** Each new build-log entry is another input, and the rules don't drift: the rubric and brand rules live in the shared layer, so changing a rule there changes every later run without touching a prompt. The passes log shows which rule tripped on which pass, so a recurring weak spot in your own drafts is visible. And the first live run (stop 10) is still waiting to replace the fixture numbers with real ones.
- **The design (no UI).** Two pieces. **The loop** (`src/post_loop/loop.py`): the cap is the `for` bound and nothing else; each pass is Writer (draft or revise) → Critic (JSON, validated against `schemas/critic_v1.json`) → gate. **The shared G0 layer** (pinned at `6f5e605`, D-6): the gate is G0's `claims.registry`, G0's claim rule (every number, URL and quote must be in the source), G0's brand policy v1 **and** `g3-skill-1`, then G0's evaluation of the rubric `g3_linkedin_post_v1`. Every call is logged to G0 observability against a $10 run cap. The loop holds no rules of its own; the prompts point at G0 (pinned by `test_prompts_carry_pointers_not_copied_rules`).

## Walk-through

Each stop says how it was verified. "Run 2026-11-24" means the exact command was run in the portfolio-pack session (unattended, fresh sandbox, `G0_DB_PATH` set to a scratch file, `--out` to a scratch folder). **Shane has not yet walked any of these stops himself.**

Verified in this session: **9 of 10 stops.** Stop 10 is the live run, which nobody has done.

### 1. Set up

```bash
uv sync --frozen
export G0_DB_PATH=/tmp/g3-demo/layer.sqlite   # optional; default is ~/.g0-shared-layer/layer.sqlite
uv run ruff check . && uv run mypy && uv run pytest
```

Expect: `All checks passed!`, `no issues found in 10 source files`, `79 passed`.
**Verified by:** the gate run 2026-11-24 (`docs/GATE-2026-11-24.md`), all exit 0.

### 2. A topic run

```bash
uv run post-loop "What a hard pass cap teaches an agent"
```

Expect: one pass, `claims=5 brand=5 hook=4 · G0 claims=clear/pass brand=pass total=1.00 → PASS`, then `topic-pass-cap: passed on pass 1 of 3.` and the paths to the draft and its passes log. Exit 0. A topic with no recording is refused with a clear message pointing at `--live` (also run 2026-11-24, exit 1).
**Verified by:** command run 2026-11-24 (exit 0); `test_cli_topic_runs_recorded`, `test_cli_unknown_topic_is_a_clear_error`.

### 3. A `--note` run (a build-log entry as the source)

```bash
uv run post-loop --note g3-post-loop
```

Expect three passes: pass 1 fails on the hook (2/5); pass 2 fixes the hook but trips the skill-seeded opener rule that G0 v1 alone would miss (`brand=fail`); pass 3 passes (`total=1.00`). Exit 0.
**Verified by:** command run 2026-11-24 (exit 0); `test_every_case_matches_its_expected_outcome[g3-third-pass]`, `test_brand_gate_requires_both_versions`.

### 4. A `--case` run (a deliberately weak draft improves)

```bash
uv run post-loop --case weak-draft-improves
```

Expect hook 1 → 3 → 4 and G0 total 0.60 → 0.80 → 1.00, passing on pass 3. This is acceptance criterion 1. Exit 0.
**Verified by:** command run 2026-11-24 (exit 0); `test_ac1_weak_draft_improves_with_scores_logged`.

### 5. The pass cap

```bash
uv run post-loop --cap 5 --case g0-pass-first
```

Expect a refusal: `--cap 5 is above the provisional cap of 3 (D-2); add --allow-cap-above-3 to permit it`. Exit 1. No case, at any cap from 1 to 3, makes more passes than the cap or more Critic calls than passes (acceptance criterion 2).
**Verified by:** command run 2026-11-24 (exit 1); `test_cli_refuses_cap_above_3_without_flag`, `test_ac2_never_exceeds_the_cap`, `test_ac2_cap_must_be_positive`.

### 6. A needs-human-review case

```bash
uv run post-loop --case weak-draft-cap
```

Expect three failing passes (hook never reaches 4), then `weak-draft-cap: NEEDS HUMAN REVIEW — cap of 3 hit after 3 passes`. Exit **2**. Open the draft file: its front matter says `status: needs_human_review`, `stop_reason: cap_hit`, `measured_live: false`, `posted: false`. Acceptance criterion 4.
**Verified by:** command run 2026-11-24 (exit 2, front matter read); `test_cli_cap_hit_exit_code_2`, `test_ac4_cap_hit_is_flagged_not_silent`.

### 7. An unsupported claim never passes, even when the Critic says it does

```bash
uv run post-loop --case unsupported-claim
```

Expect `G0 claims=unsupported/fail` on every pass. On pass 2 the recorded Critic says pass and is overruled: `(Critic pass overruled by G0)`. Ends needs human review, exit 2. Acceptance criterion 3 and D-10.
**Verified by:** command run 2026-11-24 (exit 2); `test_ac3_unsupported_claim_never_passes_even_when_critic_says_pass`, `test_ac3_any_unsupported_number_fails_even_if_the_rest_is_perfect`.

### 8. A malformed Critic answer is caught

```bash
uv run post-loop --case malformed-critic
```

Expect pass 1 `Critic output INVALID … not JSON`, pass 2 `INVALID … scores.hook: Input should be less than or equal to 5`, the same draft re-checked, and a pass on pass 3. Acceptance criterion 5 and D-12.
**Verified by:** command run 2026-11-24 (exit 0); `test_ac5_malformed_critic_is_caught_and_fails_closed`, `test_malformed_is_caught` (12 malformed shapes), `test_malformed_on_last_pass_ends_in_review`.

### 9. The eval report

```bash
uv run post-loop eval --out /tmp/g3-demo/out --report /tmp/g3-demo/eval-report.md
```

Expect 9 cases, `avg passes to pass: 2.14 · cap-hit rate: 0.2222`, and a report that, below its header, matches `docs/eval-report.md`. These numbers come from the **hand-written recorded responses**, not a model. (Leave out `--report` and it overwrites `docs/eval-report.md`.)
**Verified by:** the CI eval step run 2026-11-24 (exit 0, report body identical to the committed one); `test_eval_report_numbers`.

### 10. The live run (optional, costs money)

```bash
# ANTHROPIC_API_KEY in a gitignored .env, exported
uv run post-loop --note g3-post-loop --live
```

At most 6 model calls for one case (3 Writer, 3 Critic); G0's $10 run cap applies. Without a key the CLI refuses `--live`.
**Not run.** Never run by anyone; not yet run by Shane. Only the refusal without a key is verified, by `test_cli_live_refused_without_key` and `test_live_caller_refuses_without_a_key` (in the 79 passing tests).
