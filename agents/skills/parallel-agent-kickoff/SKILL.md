---
name: parallel-agent-kickoff
description: Use when clustering issues/PRs that look similar and creating a single agent session for each group. Triggers include requests to kick off, start, spawn, launch, or create parallel sessions; run sequential Socratic prompts with crystallization, plainerization, or simplification; auto-triage in the same session without editing or writing on the PR; or leave mostly maintainer decision making for local fix vs good global solution, proof, duplicate, close, land, or rework calls.
---

# Parallel Agent Kickoff

Use this skill to cluster issues/PRs that look similar, then create a single agent session for each group.

When the session is kicked off, drive it with sequential prompts for Socratic questioning: crystallization, plainerization, and simplification. Then auto-triage in that same session without editing or writing on GitHub. The handoff should leave mostly decision making: duplicate or separate, local fix or good global solution, enough proof or more repro, land or rework, close or keep open.

## Default Rules

- Cluster first. Put issues/PRs that look similar into a single session when they may share the same bug.
- Create individual sessions only when items are related but need separate code/proof decisions.
- Keep GitHub mutation out of these sessions unless the user explicitly asks for comments, labels, assignment, closing, or PR creation.
- Use the requested working directory exactly. If the user says the sessions must start in a repo, include that directory in every kickoff prompt.
- Include the known summary and live repro result in the first prompt.
- Treat "plain language" as a comprehension check: what does the agent mean, exactly, and does the explanation make sense?
- Distinguish source inspection, unit proof, synthetic repro, live local repro, reported-environment repro, and production proof.
- When the user asks for visible sessions, use visible/session UI-capable launch options if available. Otherwise, say so and provide the prompts ready to paste.

## Workflow

1. Gather the issue/PR set.
   - List each item as `(issue)` or `(PR)`.
   - Capture title, current state, linked items, current assignee if relevant, and known summary.
   - Capture the live repro result exactly, including "not live", "synthetic only", "blocked", or "not reproduced".

2. Cluster by likely root cause.
   - Group together items that share the same causal mechanism.
   - Keep adjacent-only items separate, even if they share keywords or a subsystem.
   - Use the mechanism as the cluster name.

3. Crystallize the root-cause hypothesis for each cluster.
   - State what breaks for the user.
   - State what the system is doing internally.
   - State which evidence supports the hypothesis.
   - State which part is still uncertain.

4. Immediately judge local fix vs good global solution.
   - Say whether the known PR/fix is a local/narrow fix, a good global solution, or a repro/proof artifact.
   - If local, say its coverage and remaining gaps.
   - If global, say what contract or ownership boundary makes it global.
   - If proof-only, say what implementation decision it enables.

5. Kick off one session per cluster.
   - Use the kickoff prompt template below.
   - If multiple sessions can be started in parallel, start them in parallel.
   - If the session tool is unavailable, create the prompts and tell the user which sessions failed to launch.
   - Keep the session read-only unless the user explicitly asks for mutations.

6. Drive Socratic follow-up prompts sequentially in that same session.
   - Treat the kickoff prompt as starting context.
   - After the first agent response, send the follow-up prompts in order when the session answer is vague, proof-light, or decision-incomplete.
   - Stop early only when the session already answers the decision packet clearly.

## Kickoff Prompt Template

Use this structure for each session. Fill in concrete item numbers and evidence.

```text
Working directory: <absolute repo path>. Start from that directory and stay in that repository.

Cluster: <short mechanism name>

Items:
- #12345 (issue) - <title>. Summary: <one sentence>. Live repro result: <exact proof status>.
- #12346 (PR) - <title>. Summary: <one sentence>. Live repro result: <exact proof status>.

Initial root-cause hypothesis / crystallization:
<plain-language mechanism; include uncertainty>

Initial local-fix-vs-good-global-solution judgment:
<say whether the current fix/PR is local, a good global solution, or proof-only, and why>

Task:
Inspect the current code, issue/PR state, linked work, and available proof. Determine whether these items share one bug or should stay separate. Explain the root cause in plain language, then judge whether the available solution is a local fix or a good global solution. Identify what proof is already available, what proof is missing, what would be overkill, and what maintainer decision remains.

Keep GitHub and files unchanged unless explicitly asked. If you find a proposed comment or close/land recommendation, write it as draft text only.
```

## Sequential Follow-Ups

Use these as follow-up prompts inside the same session. Send the next one only after reading the previous response.

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
Plainer. Rewrite the explanation as if the previous answer did not make sense to the maintainer.

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

### 4. Simplification

```text
Simplify the decision.

In one sentence each:
- the decision left for the maintainer
- the recommended action
- the main reason
- the biggest proof gap
```

### 5. Relationship Map

```text
Map the related issues/PRs. Which are duplicates, which share the same root cause, which are adjacent only, and which are unrelated? If a single PR could fix multiple items, say exactly which ones and why.
```

### 6. Concept Boundary Check

```text
Which nearby concepts are easy to confuse with this bug? Separate synthetic repro vs live repro, idle/stall timeout vs hard timeout, slow model vs event-loop block, channel workaround vs core contract, and adjacent PR vs actual fix path where relevant.
```

### 7. Proof Test

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

### 8. Boundary And Breakage

```text
If we implement the global solution, what could break? Name affected contracts, plugin boundaries, config settings, SDK surfaces, tests, or existing consumers. Say whether this needs a staged migration or can be a direct fix.
```

### 9. Auto-Triage, No Mutation

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
- sessions started or prompts prepared
- one-line reason for each grouping
- local fix vs good global solution judgment for each cluster
- proof status for each cluster
- any visible sessions that failed to launch
