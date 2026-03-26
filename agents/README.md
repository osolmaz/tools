# Agents

This directory holds the prompt and workflow docs used for agent-driven PR automation in this repo.

## Layout

- `prompts/`
  Single-agent prompt files.
- `workflows/`
  Higher-level routing docs that explain how the prompts fit together.

## Prompts

- `prompts/implement-plan.md`
  Use this when you already have one implementation plan and want one agent to execute it end-to-end, test it, run review, check CI/CD, and report back.

- `prompts/pr-issue-triage.md`
  Use this for intake and judgment. It can process multiple PRs, issues, or raw issue descriptions in one run and decide whether the work should close, escalate, or continue autonomously.

- `prompts/land-ready-pr.md`
  Use this only after triage says a PR is safe to continue autonomously. It is for one PR at a time.

## Workflows

- `workflows/pr-automation.md`
  Describes how the triage and landing prompts work together for PR automation.
