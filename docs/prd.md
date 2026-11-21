# G3 Post Quality Loop — PRD v0.1

Nov 3, 2026 · @Shane LaBounty

## Summary

Agentic AI track, build-log G3. A Writer drafts a LinkedIn post, a Critic scores it against a rubric, and the loop repeats until the post passes or hits a pass limit. This is the first agent that pursues an objective instead of filling one request.

Built twice: **G3·B in n8n first**, then **G3·C in Python with the Claude Agent SDK**.

**From the build-log card (already set):** evaluator–optimizer pattern; Critic returns a JSON score; loop with a pass cap as the stop condition; rubric = claims verified, on-brand, has a hook; graphic row "Goal"; the rubric lives in the shared evaluation capability (G0), not inside the loop.

**Everything else here is a proposal.**

## Why it's in the portfolio

It shows goal-seeking behavior with a hard stop, and it answers a question most AI demos skip: how many passes does a draft actually need, and does each pass improve it? It also fits your existing LinkedIn workflow, since you've published roughly 90 posts from build-log write-ups.

## Flow

1. **Input:** a topic or a source note (e.g., a build-log entry).
2. **Writer** drafts the post.
3. **Critic** scores it against the rubric and returns JSON.
4. **If** every criterion passes → done. **If not** and passes are left → Writer revises using the Critic's notes. **If** the cap is hit → stop and flag for human review.
5. **Output:** final draft, every pass's score, and the reason it stopped.

## Rubric (proposed shape)

| Criterion | Check | Pass rule |
| --- | --- | --- |
| Claims verified | Every factual claim matches the shared claims registry or has a source | No unsupported claims |
| On-brand | Voice and banned-phrase rules from the shared brand policy | No violations |
| Has a hook | First line gives a reason to keep reading | Critic scores 4 or more out of 5 |

Critic output (proposed): `{ "pass": false, "scores": { "claims": …, "brand": …, "hook": … }, "fixes": ["…"] }`

## Shared-layer hooks

- **evaluation:** holds the rubric (set on the build-log card).
- **claims.registry** and **brand.policy:** the Critic checks against these rather than its own copies.
- **observability:** logs each pass's score, tokens and cost.

If G0 isn't built yet, stub these with the same input and output shape.

## G3·B (n8n) build notes

- Manual or form trigger with the topic
- Writer AI Agent → Critic AI Agent with structured JSON output → If node
- A pass counter in workflow state; the If node loops back while under the cap
- Final node saves the draft to Google Drive (matches where G1's digest goes)

## G3·C (code) build notes

- CLI: `post-loop "topic"`
- Your own loop: structured Critic output validated against a schema, stop on pass or after N tries
- Every pass logged with scores
- Report: average passes to pass, and how often the cap is hit

## Acceptance criteria (proposed)

1. A deliberately weak draft improves across passes, with scores logged each time.
2. The loop never exceeds the pass cap.
3. A draft with an unsupported claim never passes.
4. Hitting the cap produces a "needs human review" flag, not a silent best effort.
5. **C only:** a malformed Critic response is caught by schema validation, not passed through.

## Decisions needed (one at a time)

**1. Pass cap** *Recommendation: 3.* It's enough to show improvement while keeping cost per post low; the C version's data will tell you if it should change.

**2. Writer and Critic on the same model or different ones?** *Recommendation: same model first,* then test a different Critic model in G3·C as a measured comparison. That comparison is a good LinkedIn post on its own.

**3. Input source** *Recommendation: build-log entries,* since that's your real content pipeline.

## Questions for you

1. Do you have written brand rules for your LinkedIn voice (e.g., from the personal-brand skill) to seed the brand policy?
2. Should passing drafts go into your post ledger automatically, or stay as drafts for you to approve?
