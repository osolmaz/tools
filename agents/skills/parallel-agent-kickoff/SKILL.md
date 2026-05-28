---
name: parallel-agent-kickoff
description: Use as a top-level orchestrator when clustering issues/PRs that look similar and creating a standalone agent session for each group. Triggers include requests to kick off, start, spawn, launch, or create parallel Codex/Claude/Pi sessions; run sequential Socratic prompts with crystallization, plainerization, or simplification; drive read-only auto-triage in each child session without editing or writing on the PR; or keep prompting child sessions until they are ready for human takeover with mostly maintainer decision making left.
---

# Parallel Agent Kickoff

Use this skill to cluster issues/PRs that look similar, then create a single agent session for each group.

When the session is kicked off, drive it with sequential prompts for Socratic questioning: crystallization, plainerization, and simplification. Then auto-triage in that same session without editing or writing on GitHub. The handoff should leave mostly decision making: duplicate or separate, local fix or good global solution, enough proof or more repro, land or rework, close or keep open.

## Orchestrator Contract

This skill is addressed to the top-level orchestrator agent.

The orchestrator must launch standalone child sessions and drive them to a takeover-ready end state. Kickoff alone is incomplete.

- For Codex, create real Codex sessions.
- Do not use `codex exec` or one-shot command equivalents for child work. Those produce reports, not sessions the human can inspect and take over.
- If the user asks for Claude, Pi, or another agent family, use that family's standalone session mechanism instead of Codex sessions.
- Keep one child session per cluster unless the user asks for one session per item.
- Track every child session until it reaches a clear end state.
- Feed the sequential prompts into each child session as needed. The child should not stop after its first review answer when the answer is still abstract, proof-light, or missing the decision packet.
- Report session identifiers, cluster membership, current state, and the remaining human decision for every child session.

## Default Rules

- Cluster first. Put issues/PRs that look similar into a single session when they may share the same bug.
- Create individual sessions only when items are related but need separate code/proof decisions.
- Keep GitHub mutation out of these sessions unless the user explicitly asks for comments, labels, assignment, closing, or PR creation.
- Use the requested working directory exactly. If the user says the sessions must start in a repo, include that directory in every kickoff prompt.
- Include the known summary and live repro result in the first prompt.
- Treat "plain language" as a comprehension check: what does the agent mean, exactly, and does the explanation make sense?
- Distinguish source inspection, unit proof, synthetic repro, live local repro, reported-environment repro, and production proof.
- Use real Codex sessions for Codex work. If no standalone session mechanism is available, say so and provide the prompts ready to paste.

## Workflow

1. Gather the issue/PR set.
   - List each item as `(issue)` or `(PR)`.
   - Capture title, current state, linked items, current assignee if relevant, and known summary.
   - Capture the live repro result exactly, including "not live", "synthetic only", "blocked", or "not reproduced".

2. Cluster by likely root cause.
   - Group together items that share the same causal mechanism.
   - Keep adjacent-only items separate, even if they share keywords or a subsystem.
   - Use the mechanism as the cluster name.

3. Kick off one standalone session per cluster.
   - Kickoff happens here, after clustering.
   - Use the kickoff prompt template below.
   - If multiple standalone sessions can be started in parallel, start them in parallel.
   - If the session tool is unavailable, create the prompts and tell the user which sessions failed to launch.
   - Keep the session read-only unless the user explicitly asks for mutations.

4. Drive the child sessions through the triage arc.
   - Crystallize the root cause.
   - Immediately judge local fix vs good global solution after root-cause finding.
   - Plainerize and simplify when the answer is abstract or hard to follow.
   - Map related refs, classify proof, check boundaries, and end with a decision packet.

5. Drive Socratic follow-up prompts sequentially in that same session.
   - Treat the kickoff prompt as starting context.
   - Send one follow-up prompt at a time.
   - Wait for the child session's answer before sending the next prompt.
   - After the first agent response, send the follow-up prompts in order when the session answer is vague, proof-light, or decision-incomplete.
   - Stop early only when the session already answers the decision packet clearly.

6. Drive every child session to human takeover.
   - Poll or inspect every child session until it answers the decision packet.
   - Send the next Socratic prompt when a child session stalls at a generic review, skips proof classification, or fails to say local fix vs good global solution.
   - Mark a session takeover-ready only when the human can decide the next action without asking the child to explain the basics again.
   - Continue until all child sessions are takeover-ready, blocked for a concrete reason, or explicitly paused by the user.

## Kickoff Prompt Template

Use this structure for each session. Fill in concrete item numbers and evidence.

```text
Working directory: <absolute repo path>. Start from that directory and stay in that repository.

Cluster: <short mechanism name>

Why these refs are grouped:
<brief, abstract rationale for why these issues/PRs look similar>

Items:
- #12345 (issue) - <title>. Summary: <one sentence>. Live repro result: <exact proof status>.
- #12346 (PR) - <title>. Summary: <one sentence>. Live repro result: <exact proof status>.

Task:
Inspect the current code, issue/PR state, linked work, and available proof. First decide whether these items really belong in one session or should split. Then crystallize the root cause in plain language. After that, judge whether the available/current solution is a local fix or a good global solution. Identify what proof is already available, what proof is missing, what would be overkill, and what maintainer decision remains.

Keep GitHub and files unchanged unless explicitly asked. If you find a proposed comment or close/land recommendation, write it as draft text only.

End state:
Continue in this standalone session until you produce the full maintainer decision packet. The top-level orchestrator will keep prompting you if the answer is too abstract, missing proof classification, or missing the local fix vs good global solution judgment.
```

## Sequential Follow-Ups

Use these as follow-up prompts inside the same child session.

Each fenced block is one prompt turn. Send one block, read the child session's answer, then decide whether to send the next block. Do not batch multiple follow-up blocks into one message.

### 1. Crystallization

```text
Crystallize the bug.

Answer:
- what is broken
- who sees it
- what triggers it
- what component causes it
- why it happens
- what a correct fix would change
```

### 2. Plainerization

```text
Write it plainer and shorter.

Use short sentences. If you use terms like async, streaming, timeout, memory, fallback, lifecycle, gateway, cache, delivery, boundary, contract, or production-ready, define the concrete mechanism.
```

### 3. Local Fix Vs Good Global Solution

```text
Is this a local fix or a good global solution?

Answer plainly:
- what exact failure it fixes
- what remains uncovered
- whether it is provider/channel/model-specific
- where the real fix should live: core, plugin/channel/provider code, docs, tests, or config
- whether the global version would break existing behavior
```

### 4. Production Ready Solution

```text
What is the most elegant and long term production ready solution?
```

### 5. Holy Grail Check

```text
Is that the holy grail?
```

### 6. Simplification

```text
Simplify the decision.

In one sentence each:
- the decision left for the maintainer
- the recommended action
- the main reason
- the biggest proof gap
```

### 7. Relationship Map

```text
Map the related issues/PRs. Which are duplicates, which share the same root cause, which are adjacent only, and which are unrelated? If a single PR could fix multiple items, say exactly which ones and why.
```

### 8. Concept Boundary Check

```text
Which nearby concepts are easy to confuse with this bug? Separate synthetic repro vs live repro, idle/stall timeout vs hard timeout, slow model vs event-loop block, channel workaround vs core contract, and adjacent PR vs actual fix path where relevant.
```

### 9. Proof Test

```text
Classify the evidence:
- source inspection
- unit test
- synthetic repro
- local live repro
- remote/live environment repro
- CI proof
- blocked/unproven

What proof is enough for a maintainer decision here? What proof would be ideal but unnecessary?
```

### 10. Boundary And Breakage

```text
If we implement the global solution, what could break? Name affected contracts, plugin boundaries, config settings, SDK surfaces, tests, or existing consumers. Say whether this needs a staged migration or can be a direct fix.
```

### 11. Auto-Triage, No Mutation

```text
Give a maintainer triage recommendation without mutating GitHub.

Choose one:
- close as resolved
- keep open
- land existing PR
- request changes
- open broader issue
- open repro PR
- implement in same PR
- split work after diff review
- needs human product/architecture decision

Then give the decision packet:
- plain bug summary
- root cause
- local fix vs good global solution judgment
- grouped issues/PRs
- proof we have
- proof missing
- enough proof vs overkill
- recommended next action
- decision left for the maintainer
- draft GitHub comment only if useful
```

## Common Failure Guards

- If the agent says "async" or "streaming", force it to explain the blocking mechanics.
- If the agent says "timeout", force it to separate idle/stall detection, hard wall-clock timeout, provider heartbeat, and operator-configured budget.
- If the agent says "memory leak", force it to separate retained process memory from expected durable history/artifact growth.
- If the agent says "live repro", force it to name the real process, real provider/channel, environment, and observed before/after behavior.
- If the agent pulls in the current branch's PR as "this PR", verify the user actually meant that PR.
- If the agent requires a large environment-specific repro, ask whether that proof is necessary for the exact bug claim or whether it is proving a broader support claim.
- If a channel/plugin-specific PR reveals a product rule, reframe the global fix as a core contract first and the channel as one proving case.

## Output Shape

When reporting back to the user, keep it decision-focused:

- clusters created
- standalone sessions started or prompts prepared
- session identifiers and current state for each child session
- one-line reason for each grouping
- local fix vs good global solution judgment for each cluster
- proof status for each cluster
- decision left for the human
- any standalone sessions that failed to launch
