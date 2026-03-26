# PR automation workflow

This file defines how the prompts are used together.

The prompts tell a single agent what to do.
This workflow tells the system how to route work between prompts.

## The two lanes

- `prompts/pr-issue-triage.md`
  Use this for intake and judgment.
  It may process multiple PRs, issues, or raw issue descriptions in one run.

- `prompts/land-ready-pr.md`
  Use this only after triage says a PR is safe to continue autonomously.
  It must process exactly one PR per run.

## Plain-language rule

Every item starts with plain-language intent recovery.

Before deciding anything else, the agent should answer:

"What is this trying to do for a human?"

That answer should sound like a human talking to another human, not like copied ticket jargon.

## Triage lane

The triage lane is the wide intake stage.
It can handle a list of items in one run.

For each item, it should decide:

- what the real intention is
- whether that intention is valid
- whether the current PR or proposed solution actually solves the right problem
- whether a refactor is needed
- whether that refactor is `none`, `superficial`, or `fundamental`
- whether the item is safe to continue autonomously or needs human attention

## Refactor rule

- `none`
  No refactor is needed.

- `superficial`
  Local cleanup or reshaping is needed, but the work can still stay on the autonomous lane.

- `fundamental`
  The approach is wrong-shaped for the problem and needs deeper restructuring, reframing, or architecture work.
  This sends the item to the human-attention lane.

## Human-attention lane

If an item needs human attention, the autonomous flow stops early.

Do not spend time on:

- local AI review loops
- code-fixing passes
- CI cleanup
- landing preparation

Instead, post a clear human-facing comment that explains:

- the plain-language intention
- why the current work is not ready
- whether a fundamental refactor is needed
- what decision, reframing, or direction is needed from a human

## Autonomous lane

Only items marked safe to continue autonomously may enter the landing flow.

Those items may still need:

- implementation work
- superficial refactors
- local testing
- AI review
- CI cleanup

## Concurrency model

- Triage agents may process multiple items in one run.
- Landing agents must process exactly one PR in one run.
- One landing agent owns one PR until that run is finished.
- Do not batch multiple PRs into one landing run.
- Do not switch a landing agent from one PR to another mid-run.

## Handoff contract

The output of triage is the input to landing.

A PR may enter the landing lane only if triage has already concluded all of the following:

- the intention is clear
- the intention is valid
- the PR is solving the right problem in a meaningful way
- any required refactor is `none` or `superficial`
- no human framing or architectural decision is still needed

## Landing lane

The landing lane is for one PR at a time.

The landing agent should:

- finish the remaining work
- perform any superficial refactor that is needed
- test the PR
- push the latest commits
- run AI review on the current PR head
- fix valid P0 and P1 findings until none remain
- check CI/CD
- separate related failures from unrelated failures
- post a final report on the PR

If the landing agent discovers that the PR really needs a fundamental refactor after all, it should stop and send the PR back to the human-attention lane.

## End states

Each item should end in exactly one of these states:

- `escalate to human`
- `continue autonomously`
- `ready to land`

`ready to land` does not mean auto-merge.
It means the PR has passed the autonomous workflow and is ready for an explicit landing step.

## Comments

For real PRs and issues, the final result should be posted back onto the item itself as a comment.

That comment should be written in plain language and should include:

- the intention
- whether the work solves the right problem
- whether a refactor is needed and what kind
- whether human attention is required
- AI review status
- CI/CD status
- the final recommendation
