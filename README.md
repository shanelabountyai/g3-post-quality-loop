# g3-post-quality-loop — Post Quality Loop (G3·C)

Build log G3, Agentic AI track. A **Writer** drafts a LinkedIn post, a **Critic** scores it, and the loop repeats until the post passes or hits a **hard pass cap of 3**. Hitting the cap flags the draft **needs human review** instead of shipping a best effort. Nothing is posted anywhere: the output is a draft file.

This is a portfolio sample build. It runs on **hand-written recorded model responses** (no API key, no live call, no spend; D-9). The numbers below describe those fixtures, not a model.

Spec: `docs/prd.md` · decisions: `docs/DECISIONS.md` · backlog: `docs/BACKLOG.md` · eval: `docs/eval-report.md` · state and hand steps: `NEXT.md`. Only the code version is built here; the n8n version (G3·B) is the owner's hand build (D-1).

## How it works

```
post-loop "topic" | --note <id> | --case <id>
  │
  ├─ G0 health first (degraded layer or missing G3 seed → stop before any model call)
  │
  └─ for n in 1..cap (3):
       Writer   draft from the source, or revise with last pass's fixes   (skipped if the last Critic output was malformed)
       Critic   raw JSON ─► parse_critic() ─► CriticVerdict  ─ invalid ─► pass fails closed, same draft next pass
       G0 gate  claims_registry(draft)                       → no `unsupported`
                evaluation(claim_rule_v1, draft, context=source)  → every number/URL/quote is in the source
                brand_policy(draft, linkedin, v1) AND brand_policy(…, g3-skill-1)
                evaluation(g3_linkedin_post_v1, {post, claims…, brand, hook_score})  → G0 decide()
       passed = Critic.pass AND G0 passed            stop on pass
  cap hit → status: needs_human_review, exit 2
  every Writer/Critic call → G0 observability (tokens, cost, run total, $10 cap) · end of case → G0 measurement post_loop.finished
  out/<run_id>/<case>.md (draft + status) and <case>.passes.json (every pass: scores, G0 results, fixes, usage)
```

| File | What |
|---|---|
| `src/post_loop/loop.py` | The loop and the G0 gate. The cap is the `for` bound and nothing else. |
| `src/post_loop/models.py` | `CriticVerdict` (the Critic schema, D-11), `parse_critic`, `PassRecord`, `LoopResult`. |
| `src/post_loop/layer.py` | The one G0 adapter (in-process, pinned SHA). Seeds the G3 rubric and brand policy through G0's loader, `g3`-namespaced only (D-7). |
| `src/post_loop/prompts.py` | Writer and Critic specs: one-line pointers to G0, no copied rules (pinned by a test). Same model for both (D-3). |
| `src/post_loop/llm.py` | `RecordedCaller` (used), `AgentSdkCaller` (Claude Agent SDK `query`, structured output; implemented, never run here), `RecordingCaller`. |
| `src/post_loop/output.py` | The only sink: files under `out/`. No network client is imported anywhere in the package (test). |
| `src/post_loop/report.py`, `cli.py` | `post-loop eval` → average passes to pass, cap-hit rate, per-case trace. |
| `rubrics/g3_linkedin_post_v1.json` | The PRD rubric as a G0 rubric: claims verified, on-brand, hook ≥ 4/5 (`field_in:hook_score:4,5`). |
| `brand/brand_policy_g3_skill_1.json` | Brand rules from the owner's personal-brand skill that G0 v1 lacks (D-4). |
| `schemas/critic_v1.json` | The published Critic schema (equals the model; test). |
| `fixtures/` | 6 build-log source notes, 9 cases, hand-written recorded responses, and the script that writes them. |

## Shared layer (G0)

Pinned to `shanelabountyai/g0-shared-layer@6f5e605` like G2·C (D-6). The rubric lives in G0's `evaluation` store; the Critic's claims and brand opinions are re-checked against G0 `claims.registry` and `brand.policy`, never against copies in a prompt. G0's v1 contracts have no rubric/policy register tool, so the two G3 seeds go in through G0's own seed loader (the same documented exception G2 makes; D-7).

## Acceptance (PRD) — where each is proved

| AC | Test |
|---|---|
| 1 A weak draft improves across passes, scores logged | `test_ac1_weak_draft_improves_with_scores_logged` (hook 1→3→4, G0 total 0.60→0.80→1.00) |
| 2 Never exceeds the cap | `test_ac2_never_exceeds_the_cap` (every case × cap 1, 2, 3; Critic calls = passes ≤ cap) |
| 3 Unsupported claim never passes | `test_ac3_*` (including a recorded Critic false positive overruled by G0) |
| 4 Cap → "needs human review" | `test_ac4_*`, `test_cli_cap_hit_exit_code_2`, draft front matter `status: needs_human_review` |
| 5 Malformed Critic output caught | `tests/test_critic_schema.py` (12 malformed shapes), `test_ac5_malformed_critic_is_caught_and_fails_closed` |

## Running it

```bash
uv sync --frozen
uv run ruff check . && uv run mypy && uv run pytest
uv run post-loop "What a hard pass cap teaches an agent"   # recorded topic → out/<run>/topic-pass-cap.md
uv run post-loop --case weak-draft-cap                    # cap hit → exit 2, needs human review
uv run post-loop eval                                     # all cases → docs/eval-report.md
```

`G0_DB_PATH` sets the shared layer's SQLite file (default `~/.g0-shared-layer/layer.sqlite`). `--live` needs `ANTHROPIC_API_KEY` and was not used in this build.
