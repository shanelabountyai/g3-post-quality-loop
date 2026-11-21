# Kickoff — Post Quality Loop (Build Log G3, Agentic AI track)

Paste the block below into Claude Code started in `~/Projects/agentic-track/g3-post-quality-loop`, on Fable (`/model`).

```
You are starting a new build: Post Quality Loop (Build Log G3, Agentic AI track,
graphic row "Goal"). The spec is docs/prd.md. Read it fully before doing anything.
Also read ../README.md for the track order and the shared-layer (G0) contract rule.

The project is built twice, in this order:
- G3·B (n8n first): n8n: manual/form trigger -> Writer AI Agent -> Critic AI Agent (structured JSON) -> If node looping back under a pass counter; final draft saved to Google Drive.
  Deliver it as importable workflow JSON in n8n/, with a README on how to import it
  into the owner's self-hosted n8n.
- G3·C (code second): Python 3.12 + Claude Agent SDK CLI `post-loop "topic"`: own loop, Critic output validated against a schema, stop on pass or after N tries, every pass's scores logged.
  Start G3·C only after G3·B passes its acceptance criteria.

Test data: 5-10 source notes (build-log entries) plus 2-3 deliberately weak drafts and one draft with an unsupported claim.

Safety invariants (land with tests BEFORE any code path can reach a live system):
Nothing is posted anywhere. Output is a draft file only. Hitting the cap flags for human review.

Shared layer (G0): the PRD lists the shared capabilities this project calls
(claims.registry, brand.policy, audience.consent, measurement, evaluation,
observability). If ../shared/ does not exist yet, build local stubs with the same
input and output shape, in one clearly named module, so they can be swapped for G0
later. Never copy rules into an agent's prompt that belong in the shared layer.

Open decisions in the PRD: Pass cap (PRD recommends 3), same vs different Critic model, brand rules source (personal-brand skill?), whether passing drafts go to the post ledger.
Take the PRD's recommendation for each unless I say otherwise, and record each as a
D- entry in docs/DECISIONS.md before writing code.

Working rules:
- Confirm current Claude model IDs and prices from Anthropic's docs before using them.
  Confirm current n8n node names and options from n8n's docs; record what you found.
- Log tokens and cost per run from the first live call. Hard cap: $10 of live model
  calls for the whole build unless I raise it.
- Keep NEXT.md current, matching the other build-log repos: what is done, what is
  next, and exact hand steps for the owner.
- Commit at the end of every task with a clear message. Never commit secrets; keys
  live in a gitignored .env.
- Work on a branch named `kickoff`. No merges to main, no deploys, no live external
  writes, and no account changes without my explicit go.

Step 1, plan first: write docs/BACKLOG.md breaking G3·B then G3·C into tasks
you can finish and test in one sitting, each with acceptance criteria taken from the
PRD. List owner hand steps separately. Then stop and show me the backlog and
DECISIONS.md before building.
```
