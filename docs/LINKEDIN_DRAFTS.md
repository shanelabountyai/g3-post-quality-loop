# LinkedIn drafts — G3·C Post Quality Loop

Two drafts in Shane's voice, each built on one decision from `docs/DECISIONS.md`. Both are **Drafted, unposted**. Nothing here has been posted anywhere, and nothing in this repo can post.

Checked on 2026-11-24 against the loop's own brand gate (G0 brand policy v1 **and** `g3-skill-1`, channel `linkedin`): both pass (244 and 253 words; none of the brief's banned phrases). How it was run is in D-22. That check is a rule check, not a read for voice; edit freely.

---

## Draft 1 — the AI judge doesn't get the last word (D-10)

**Status: Drafted, unposted**

My critic agent approved a post with a made-up number in it.

That was on purpose. I wrote that test case to see what my post-checking loop would do when the AI judge gets it wrong.

The setup: a Writer agent drafts a LinkedIn post, a Critic agent scores it, and the loop tries again until it passes or hits three tries. The easy design is to let the Critic decide.

I didn't. A draft passes only when the Critic says pass AND a set of plain rule checks agree: every number, link and quote has to appear in the source note, and every claim has to clear a shared claims list.

In the test, the Critic said "pass" on the second try. The rule checks said no, because the number wasn't in the source. The rules won, the loop used its third try, and the draft came out flagged "needs human review" instead of looking finished.

It works the other way too. If the Critic fails a draft the rules would pass, it stays failed. The model can catch things a rule can't, like a flat opening line. It just can't approve a fact on its own.

All of this ran on hand-written test responses. No real model has scored a draft yet. That run comes next, and I want to see how often a real Critic gets overruled.

Where do you let the model have the final say, and where don't you?

---

## Draft 2 — a garbled answer still costs a try (D-12)

**Status: Drafted, unposted**

What should an agent loop do when the judge answers in prose instead of JSON?

My post-checking loop asks a Critic agent for a small JSON verdict: pass or fail, three scores from 1 to 5, and a list of fixes. Sometimes a model answers "Looks good to me!" instead. Sometimes it sends JSON with a 7 on a 5-point scale.

I had three options:

1. Retry inside the same try until the answer is clean.
2. Treat a messy answer as a pass.
3. Count it as a failed try and move on.

Option 2 was out from the start. Option 1 sounds friendly but it's how a loop with a hard cap of three quietly stops having one.

I picked 3. A garbled verdict fails closed and uses up its try. The draft isn't revised, because there are no fixes worth trusting, and the next try re-checks the same draft. If the last try is the garbled one, the post is flagged for human review.

The test case for this has a Critic that answers in prose on try one, sends a score of 7 on try two, and gets it right on try three. Both bad answers are caught and logged, and the post passes on the third try.

That case runs on hand-written responses, not a real model. I'd rather know the cap holds before I spend a cent finding out how often a real model breaks format.

How do you handle a model that ignores the output format?
