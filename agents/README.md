# Agents

This directory holds the prompt and workflow docs used for agent-driven PR automation in this repo.

## Layout

- `skills/`
  Repo-local skills that package the prompts and workflow docs into reusable execution guides.
- `sync-skills.py`
  Synchronizes repo-local skills into Codex's skills directory as real copied files, with no symlinks.
- `prompts/`
  Single-agent prompt files.
- `workflows/`
  Higher-level routing docs that explain how the prompts fit together.

## Syncing

Run `python3 agents/sync-skills.py` to mirror all repo-local skills into `$CODEX_HOME/skills` or `~/.codex/skills`.

- Use `--dry-run` to preview changes.
- Use `--no-prune` to keep previously synced repo-managed skills that are not in the current selection.
- Pass one or more skill ids or source directory names to sync only a subset.

## Skills

- `skills/implementation-loop/`
  Use this when you already have an approved implementation plan and want one agent to finish the work, test it, run the review loop, clear valid PR feedback, and verify CI/CD before handing back a ready-to-land PR.

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
