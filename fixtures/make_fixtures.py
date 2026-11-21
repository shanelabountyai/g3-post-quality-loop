"""Writes fixtures/cases.json and fixtures/recorded.json (D-14). Hand-written test data, not model output: python fixtures/make_fixtures.py"""
import json, pathlib
root = pathlib.Path(__file__).resolve().parent

notes = {
 "g0-shared-layer": {"title": "G0 Shared Capability Layer", "text":
  "Build log G0, Shared Capability Layer. Six capabilities every agent in the track needs (claims.registry, brand.policy, audience.consent, measurement, evaluation, observability) now live behind one MCP server with versioned contracts. 157 tests run without network or a model call. A breaking contract change fails the contract tests until the version is bumped. G1's own count: 16 integrations before the layer, 8 after; 24 copies of the 8 shared rules before, 8 after."},
 "g1-signal-scout": {"title": "G1 Weekly Signal Scout", "text":
  "Build log G1, Weekly Signal Scout. Four agents in sequence (Researcher, Summarizer, Editor, Writer) read 15 RSS feeds and produce a weekly digest of items worth posting about. Built twice: n8n first, then Python with the Claude Agent SDK. The n8n version carried every shared rule in every agent's prompt; the duplication log counted 7 rules carried by more than one agent. A seen-items table makes sure a re-run never repeats an item, and items are marked seen only after the digest is written."},
 "g2-lead-triage": {"title": "G2 Lead Triage Crew", "text":
  "Build log G2, Lead Triage Crew. An orchestrator decides which specialists to call for each new lead: an Enricher, a Qualifier and a Drafter. The follow-up email is left as a draft. It never sends anything: a PreToolUse hook denies anything shaped like a send, and the HubSpot interface has no send method. All leads are synthetic. Six bands decide what happens to a lead, one rule each, in one function."},
 "g3-post-loop": {"title": "G3 Post Quality Loop", "text":
  "Build log G3, Post Quality Loop. A Writer drafts a LinkedIn post, a Critic scores it against a rubric, and the loop repeats until the post passes or hits a cap of 3 passes. Hitting the cap flags the draft for human review instead of shipping a best effort. A malformed Critic response is caught by schema validation, not passed through."},
 "rule-duplication": {"title": "Why rules moved out of prompts", "text":
  "Build log note. In G1's n8n build the brand voice rule was pasted into 2 agents and the claim rule into 4. When a rule changed, every copy had to change, and a missed copy meant two agents disagreeing about what good looks like. Moving the rules into the shared layer left one copy of each."},
 "cost-logging": {"title": "Cost logging across the track", "text":
  "Build log note. Every model call in the track is logged with its tokens and cost against a $10 cap per run. Logging is never refused, so an overrun is visible instead of hidden. The cap is checked before a model judge is called."},
}

def crit(p, claims, brand, hook, fixes=None, unsupported=None):
    d = {"pass": p, "scores": {"claims": claims, "brand": brand, "hook": hook}, "fixes": fixes or []}
    if unsupported: d["unsupported_claims"] = unsupported
    return d

R = {}
cases = []

# 1 passes on pass 1
cases.append({"id": "g0-pass-first", "note": "g0-shared-layer", "expect": {"passed": True, "passes": 1},
  "about": "Strong first draft; passes on pass 1."})
R["writer:g0-pass-first:1"] = {"post": "Three agents, six tools each, and the same brand rule pasted into every prompt. That was the plan I threw out.\n\nIn G0 the six capabilities every agent needs now sit behind one MCP server with versioned contracts. A breaking contract change fails the contract tests until the version is bumped, so nobody changes a shape by accident.\n\nThe count that sold me: 16 integrations before the layer, 8 after. 24 copies of the shared rules down to 8.\n\nAnd 157 tests run without network or a model call.\n\nWhere do your shared rules live today: in one place, or in every prompt?\n\n#marketingops #aiagents #buildinpublic"}
R["critic:g0-pass-first:1"] = crit(True, 5, 5, 4)

# 2 hook improves, passes on 2
cases.append({"id": "g1-hook-fix", "note": "g1-signal-scout", "expect": {"passed": True, "passes": 2},
  "about": "First draft has a weak hook; the revision fixes it and passes on pass 2."})
R["writer:g1-hook-fix:1"] = {"post": "This week I worked on a weekly digest project.\n\nFour agents in sequence (Researcher, Summarizer, Editor, Writer) read 15 RSS feeds and pick items worth posting about. I built it twice: n8n first, then Python with the Claude Agent SDK.\n\nThe n8n version carried every shared rule in every prompt.\n\nWhat would you build first?\n\n#marketingops #aiagents #n8n"}
R["critic:g1-hook-fix:1"] = crit(False, 5, 4, 2, ["The first line is a status update, not a reason to keep reading. Open with the duplication finding."])
R["writer:g1-hook-fix:2"] = {"post": "7 rules were carried by more than one agent. I only found out because I built the same scout twice.\n\nFour agents in sequence (Researcher, Summarizer, Editor, Writer) read 15 RSS feeds and produce a weekly digest. The n8n version carried every shared rule in every prompt; the duplication log made the cost visible.\n\nThe second build, in Python with the Claude Agent SDK, keeps one copy of each rule.\n\nOne detail I'd keep in any agent: items are marked seen only after the digest is written, so a failed run never silently drops anything.\n\nHave you ever counted how many prompts carry the same rule?\n\n#marketingops #aiagents #n8n"}
R["critic:g1-hook-fix:2"] = crit(True, 5, 5, 5)

# 3 brand violation, passes on 2
cases.append({"id": "g2-brand-fix", "note": "g2-lead-triage", "expect": {"passed": True, "passes": 2},
  "about": "First draft breaks G0 brand policy v1 ('excited to share', emoji); the revision passes on pass 2."})
R["writer:g2-brand-fix:1"] = {"post": "Excited to share my latest build \U0001F680\n\nAn orchestrator decides which specialists to call for each new lead: an Enricher, a Qualifier and a Drafter. The follow-up email is left as a draft.\n\nIt never sends anything.\n\nWhat guardrails do you put on agents?\n\n#marketingops #aiagents #hubspot"}
R["critic:g2-brand-fix:1"] = crit(False, 5, 1, 2, ["Remove 'Excited to share' and the emoji.", "Open with the guarantee: it never sends anything, enforced by the system."])
R["writer:g2-brand-fix:2"] = {"post": "My lead triage crew cannot send an email. Not told not to. Cannot.\n\nAn orchestrator decides which specialists to call for each new lead: an Enricher, a Qualifier and a Drafter. The follow-up email is left as a draft.\n\nA PreToolUse hook denies anything shaped like a send, and the HubSpot interface has no send method. A prompt is a promise; an interface without the method is a guarantee.\n\nSix bands decide what happens to a lead, one rule each, in one function. All leads are synthetic.\n\nWhere do you enforce your agent guardrails: in the prompt or in the system?\n\n#marketingops #aiagents #hubspot"}
R["critic:g2-brand-fix:2"] = crit(True, 5, 5, 5)

# 4 passes on 3 (hook, then skill brand rule)
cases.append({"id": "g3-third-pass", "note": "g3-post-loop", "expect": {"passed": True, "passes": 3},
  "about": "Pass 1 weak hook; pass 2 trips the skill-seeded opener rule (g3-skill-1) that G0 v1 does not hold; passes on pass 3."})
R["writer:g3-third-pass:1"] = {"post": "Here is an overview of the G3 build.\n\nA Writer drafts a LinkedIn post, a Critic scores it against a rubric, and the loop repeats until the post passes or hits a cap.\n\nThoughts?\n\n#aiagents #marketingops #buildinpublic"}
R["critic:g3-third-pass:1"] = crit(False, 5, 4, 2, ["Weak hook: lead with the cap and what happens when it is hit."])
R["writer:g3-third-pass:2"] = {"post": "I've been thinking a lot about when an agent should stop.\n\nA Writer drafts a LinkedIn post, a Critic scores it against a rubric, and the loop repeats until the post passes or hits a cap of 3 passes.\n\nHitting the cap flags the draft for human review.\n\nWhen should your agents stop?\n\n#aiagents #marketingops #buildinpublic"}
R["critic:g3-third-pass:2"] = crit(False, 5, 3, 4, ["The opener is a banned pattern; start with the moment, not the thinking."])
R["writer:g3-third-pass:3"] = {"post": "My agent gets 3 tries. On the fourth, a human gets the draft.\n\nA Writer drafts a LinkedIn post, a Critic scores it against a rubric, and the loop repeats until the post passes or hits a cap of 3 passes.\n\nHitting the cap flags the draft for human review instead of shipping a best effort. That flag is the feature, not the failure.\n\nAnd a malformed Critic response is caught by schema validation, not passed through as a pass.\n\nWhat's your agent's stop condition?\n\n#aiagents #marketingops #buildinpublic"}
R["critic:g3-third-pass:3"] = crit(True, 5, 5, 4)

# 5 weak draft improves across passes (AC1)
cases.append({"id": "weak-draft-improves", "note": "rule-duplication", "expect": {"passed": True, "passes": 3},
  "about": "Deliberately weak supplied draft (banned opener, 'game changer', 'Let's connect!'); scores rise each pass and it passes on pass 3 (AC 1).",
  "start_draft": "I've been thinking a lot about AI agents lately. They are a game changer for marketing teams everywhere. Let's connect!"})
R["critic:weak-draft-improves:1"] = crit(False, 5, 1, 1, ["Remove the banned opener, 'game changer' and 'Let's connect!'.", "Use the note: the brand rule was pasted into 2 agents and the claim rule into 4."])
R["writer:weak-draft-improves:2"] = {"post": "Some thoughts on agent rules.\n\nIn one build the brand voice rule was pasted into 2 agents and the claim rule into 4. When a rule changed, every copy had to change.\n\nMoving the rules into the shared layer left one copy of each.\n\nHow do you manage this?\n\n#aiagents #marketingops"}
R["critic:weak-draft-improves:2"] = crit(False, 5, 5, 3, ["The hook is generic. Lead with the cost of a missed copy."])
R["writer:weak-draft-improves:3"] = {"post": "A missed copy of one rule meant two of my agents disagreed about what good looks like.\n\nIn G1's n8n build the brand voice rule was pasted into 2 agents and the claim rule into 4. When a rule changed, every copy had to change.\n\nMoving the rules into the shared layer left one copy of each. Now a change is one commit, and every agent reads the same answer.\n\nHow many copies of your brand rules exist right now?\n\n#aiagents #marketingops #buildinpublic"}
R["critic:weak-draft-improves:3"] = crit(True, 5, 5, 4)

# 6 weak draft that never passes -> cap hit
cases.append({"id": "weak-draft-cap", "note": "cost-logging", "expect": {"passed": False, "passes": 3},
  "about": "Deliberately weak supplied draft (tenure opener, engagement bait); revisions never reach a 4/5 hook, so the cap is hit and the draft is flagged for human review (AC 4).",
  "start_draft": "With 20+ years in marketing, I know cost matters. Every call is logged. Drop a like if you agree."})
R["critic:weak-draft-cap:1"] = crit(False, 5, 1, 1, ["Lead with an outcome, not tenure.", "Remove the engagement bait."])
R["writer:weak-draft-cap:2"] = {"post": "Cost matters in AI projects.\n\nEvery model call in the track is logged with its tokens and cost against a $10 cap per run.\n\nWhat do you think?\n\n#aiagents"}
R["critic:weak-draft-cap:2"] = crit(False, 5, 5, 2, ["The hook is a truism. Lead with what happens on an overrun."])
R["writer:weak-draft-cap:3"] = {"post": "Logging matters.\n\nEvery model call in the track is logged with its tokens and cost against a $10 cap per run. Logging is never refused, so an overrun is visible instead of hidden.\n\nWhat do you think?\n\n#aiagents"}
R["critic:weak-draft-cap:3"] = crit(False, 5, 5, 3, ["Still no reason to keep reading in line one."])

# 7 unsupported claim never passes, even with a Critic false positive (AC3)
cases.append({"id": "unsupported-claim", "note": "g2-lead-triage", "expect": {"passed": False, "passes": 3},
  "about": "Supplied draft carries an unsupported claim (a registry stat with the wrong number, and a result not in the source). The Writer keeps it; on pass 2 the recorded Critic wrongly says pass. G0's claims checks overrule it every time, so it never passes and is flagged (AC 3, D-10).",
  "start_draft": "95% of organizations now use AI in at least one function, and my lead triage crew cut triage time by 73%.\n\nAn orchestrator calls an Enricher, a Qualifier and a Drafter for each new lead. It never sends anything.\n\nIs your team there yet?\n\n#aiagents #marketingops"})
R["critic:unsupported-claim:1"] = crit(False, 2, 5, 4, ["Source the 73% or remove it; it is not in the note."], ["my lead triage crew cut triage time by 73%"])
R["writer:unsupported-claim:2"] = {"post": "95% of organizations now use AI in at least one function, and my lead triage crew cut triage time by 73%.\n\nAn orchestrator decides which specialists to call for each new lead: an Enricher, a Qualifier and a Drafter. It never sends anything.\n\nIs your team there yet?\n\n#aiagents #marketingops"}
R["critic:unsupported-claim:2"] = crit(True, 5, 5, 4)
R["writer:unsupported-claim:3"] = {"post": "My lead triage crew cut triage time by 73%, and 95% of organizations now use AI in at least one function.\n\nAn orchestrator decides which specialists to call for each new lead. The follow-up email is left as a draft.\n\nIs your team there yet?\n\n#aiagents #marketingops"}
R["critic:unsupported-claim:3"] = crit(False, 2, 5, 4, ["The 73% is still unsourced."], ["my lead triage crew cut triage time by 73%"])

# 8 malformed critic output caught (AC5), passes on 3
cases.append({"id": "malformed-critic", "note": "g1-signal-scout", "expect": {"passed": True, "passes": 3},
  "about": "Pass 1 Critic returns prose instead of JSON; pass 2 returns JSON that fails the schema (a fail with no fixes, a score of 7). Both are caught and fail closed; the same draft is re-critiqued and passes on pass 3 (AC 5, D-12)."})
R["writer:malformed-critic:1"] = {"post": "Items are marked seen only after the digest is written. That one ordering rule is why a failed run never loses anything.\n\nMy weekly scout runs four agents in sequence (Researcher, Summarizer, Editor, Writer) over 15 RSS feeds. A seen-items table makes sure a re-run never repeats an item.\n\nMark too early and a crash silently drops the week. Mark after the write and the worst case is a repeat you can see.\n\nWhere does your pipeline mark work as done?\n\n#aiagents #marketingops #n8n"}
R["critic:malformed-critic:1"] = "Looks good to me! The hook is strong and the claims match the note. I'd ship it."
R["critic:malformed-critic:2"] = {"pass": False, "scores": {"claims": 5, "brand": 5, "hook": 7}, "fixes": []}
R["critic:malformed-critic:3"] = crit(True, 5, 5, 5)

# 9 topic-only input (CLI example)
topic = "What a hard pass cap teaches an agent"
cases.append({"id": "topic-pass-cap", "topic": topic, "expect": {"passed": True, "passes": 1},
  "about": "Topic-only input, as `post-loop \"What a hard pass cap teaches an agent\"`. The topic is the only source, so the draft carries no numbers."})
R["writer:topic-pass-cap:1"] = {"post": "A loop without a stop condition isn't an agent. It's a bill.\n\nWhen a Writer and a Critic go back and forth, the question isn't whether the next draft is better. It's who decides when to stop, and what happens then.\n\nA hard pass cap answers both. The agent gets a fixed number of tries, and when it runs out, a person gets the draft with a clear flag instead of a quiet best effort.\n\nWhat's the stop condition on the agents you run?\n\n#aiagents #marketingops"}
R["critic:topic-pass-cap:1"] = crit(True, 5, 5, 4)

(root / "cases.json").write_text(json.dumps({
  "_about": "G3 test data (D-14): source notes summarising real entries of this build log (facts from the g0/g1/g2 repos' READMEs and decision logs, and this repo's PRD), deliberately weak drafts, one draft with an unsupported claim, and one malformed-Critic case. `expect` is the outcome the recorded responses are written to produce; tests assert it. No client, testimonial or business result appears anywhere.",
  "notes": notes, "cases": cases}, indent=2, ensure_ascii=False) + "\n")
(root / "recorded.json").write_text(json.dumps({
  "_about": "Hand-written responses in each agent's output shape, keyed <agent>:<case>:<pass>. NOT a recording of a live model (D-9): no API key was used and no model was called. Writer entries are {post}; Critic entries are the Critic JSON, or a raw string to exercise schema validation. A first live run with --record replaces this file.",
  "responses": R}, indent=2, ensure_ascii=False) + "\n")
print(len(cases), len(R))
