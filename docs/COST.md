# Cost note — G3·C Post Quality Loop

As of 2026-11-24. **Measured figures only. Nothing here comes from a live run, because there has been none** (D-9).

## Measured

| Item | Figure | Source |
|---|---|---|
| Cost to build | **Not measured** | The repo records no build tokens or spend. |
| Running cost per post | **Not measured: no live run** | `AgentSdkCaller` has never run (D-9, NEXT.md). |
| Cost of the recorded eval | $0.0000, 0 tokens in / 0 out | `docs/eval-report.md`; re-run 2026-11-24 (`docs/GATE-2026-11-24.md`). No model was called, so this is not a cost per post. |

## Limits (not results)

These are caps and a price table the code enforces or uses. They bound what a live run could cost; they are not what one did cost.

| Limit | Value | Where |
|---|---|---|
| Passes per post | 3 | D-2; `MAX_CAP_DEFAULT` in `src/post_loop/loop.py`; the CLI refuses more without `--allow-cap-above-3`. |
| Model calls per post at cap 3 | at most 6 (3 Writer, 3 Critic) | Follows from the cap; NEXT.md 2026-11-21 "You:" step 3. |
| Model calls for a live eval of all 9 cases | at most 27 Writer + 27 Critic | NEXT.md 2026-11-21 "You:" step 3. |
| Run spending cap | $10 (env `G0_RUN_CAP_USD`) | G0 `shared_layer/capabilities/observability.py`, `DEFAULT_CAP_USD = 10.0`, at the pinned G0 commit `6f5e605` (D-6). |
| Price on file for `claude-sonnet-5-5` | $2.00 per million input tokens, $10.00 per million output tokens | G0 `shared_layer/capabilities/evaluation.py`, `PRICES_PER_MTOK`, at `6f5e605`. G1 D-35 records it as confirmed on Anthropic's pricing page; **not re-checked in this session**. |

No cost per post is estimated from these: token counts per call are unknown until a live run. The first live run (`NEXT.md`, "You:") is what turns this note into numbers.
