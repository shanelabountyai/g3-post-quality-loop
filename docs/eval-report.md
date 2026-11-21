# Eval report — G3·C Post Quality Loop

Generated 2026-11-21T01:52:42+00:00 · run `eval-recorded` · pass cap 3 · mode: recorded fixtures — hand-written responses, no model called; tokens and cost are **not measured live**.

## Headline

- **Average passes to pass: 2.14** (over the 7 cases that passed)
- **Cap-hit rate: 22%** (2 of 9 cases flagged *needs human review*)
- Most passes used by any case: 3 (cap 3)
- Malformed Critic responses caught by schema validation: 2
- Critic passes overruled by the shared layer (G0): 1
- Tokens: 0 in / 0 out · cost $0.0000 — not measured live (no API key; recorded path, D-9)

> These numbers describe the hand-written fixtures in `fixtures/recorded.json`, which were written to exercise pass-on-1, pass-on-2, pass-on-3, a cap hit, an unsupported claim and malformed Critic output. They test the loop and the governed checks, not a model. A live run (NEXT.md, "You:" steps) produces the real numbers.

## Per case

| case | outcome | passes | hook by pass | brand by pass | G0 total by pass | notes |
|---|---|---|---|---|---|---|
| `g0-pass-first` | passed | 1 | 4 | 5 | 1.00 |  |
| `g1-hook-fix` | passed | 2 | 2 → 5 | 4 → 5 | 0.80 → 1.00 |  |
| `g2-brand-fix` | passed | 2 | 2 → 5 | 1 → 5 | 0.60 → 1.00 | brand: never_use.emoji, never_use.excited_to_share |
| `g3-third-pass` | passed | 3 | 2 → 4 → 4 | 4 → 3 → 5 | 0.80 → 0.80 → 1.00 | brand: g3.opener.been_thinking_a_lot |
| `weak-draft-improves` | passed | 3 | 1 → 3 → 4 | 1 → 5 → 5 | 0.60 → 0.80 → 1.00 | brand: g3.never_use.lets_connect, g3.opener.been_thinking_a_lot, never_use.game_changer_space |
| `weak-draft-cap` | **needs human review** | 3 | 1 → 2 → 3 | 1 → 5 → 5 | 0.40 → 0.80 → 0.80 | number not in source; brand: g3.engagement_bait.if_you_agree, g3.tenure.years_plus |
| `unsupported-claim` | **needs human review** | 3 | 4 → 4 → 4 | 5 → 5 → 5 | 0.60 → 0.60 → 0.60 | Critic pass overruled by G0; registry: unsupported claim; number not in source |
| `malformed-critic` | passed | 3 | ✗ → ✗ → 5 | ✗ → ✗ → 5 | ✗ → ✗ → 1.00 | 2 malformed Critic response(s) caught |
| `topic-pass-cap` | passed | 1 | 4 | 5 | 1.00 |  |

✗ = the Critic's response failed schema validation; that pass failed closed (D-12).
