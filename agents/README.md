# Agents

This directory holds the prompt and workflow docs used for agent-driven PR automation in this repo.

## Layout

- `skills/`
  Repo-local skills that package the prompts and workflow docs into reusable execution guides.
- `AGENTS.md`
  Repo-local agent instructions that should also be mirrored into Codex and Claude Code homes.
- `sync-skills.py`
  Synchronizes repo-local skills into the Codex and Claude Code skills directories as real copied files, with no symlinks, and mirrors `agents/AGENTS.md` into Codex home (as `AGENTS.md`) and Claude Code home (as `CLAUDE.md`).
- `prompts/`
  Single-agent prompt files.
- `workflows/`
  Higher-level routing docs that explain how the prompts fit together.

## Syncing

Run `python3 agents/sync-skills.py` to mirror all repo-local skills into both agent homes:

- Codex: skills go to `$CODEX_HOME/skills` or `~/.codex/skills`, and `agents/AGENTS.md` is mirrored to `$CODEX_HOME/AGENTS.md` or `~/.codex/AGENTS.md`.
- Claude Code: skills go to `$CLAUDE_CONFIG_DIR/skills` or `~/.claude/skills`, where they load as personal skills, and `agents/AGENTS.md` is mirrored to `~/.claude/CLAUDE.md` (global user instructions).

Options:

- Use `--dry-run` to preview changes.
- Use `--skip-codex` or `--skip-claude` to sync only one destination.
- Use `--no-prune` to keep previously synced repo-managed skills that are not in the current selection.
- Pass one or more skill ids or source directory names to sync only a subset.
- Each destination keeps its own `.tools-agents-skill-sync.json` state file, so pruning is tracked per destination.

## Skills

- `skills/agent-blurb/`
  Use this when writing or reviewing copy-paste README blurbs that tell a
  coding agent how to install, configure, verify, or adopt a project workflow.

- `skills/check-ingredients/`
  Use this when evaluating a product ingredient list or safety claim for source-backed health, toxicity, pregnancy/child, regulatory, environmental, allergy, irritation, and finished-product risk context.

- `skills/conventional-commit/`
  Use this when you need to draft, rewrite, or validate a commit message or PR title using Conventional Commits, plus a concise repo-aware PR body when the task is a pull request.

- `skills/daily-work-summary/`
  Use this when summarizing one person's recent GitHub work across org repos in plain, source-linked bullets.

- `skills/online-shopping/`
  Use this when researching products to buy online, comparing listings, checking price history, verifying discounts, normalizing unit prices, evaluating sale timing, and deciding whether to buy now or wait.

- `skills/autoimplement/`
  Use this when you already have an approved implementation plan and want one agent to finish the work, test it, run the review loop, clear valid PR feedback, and verify CI/CD before handing back a ready-to-land PR.

- `skills/parallel-agent-kickoff/`
  Use this when clustering related issues or PRs and starting decision-focused
  agent sessions for each shared bug or fix-shape group.

- `skills/pi-demo-grid/`
  Use this when launching a balanced tmux grid of concurrent `localpi --demo`
  Pi sessions for demos, load demos, and side-by-side output comparisons.

- `skills/semver/`
  Use this while deciding how to choose the next major, minor, patch, or
  pre-1.0 version during release.

- `skills/write-readme/`
  Use this when creating, rewriting, or reviewing README files so they stay focused on users, not maintainer process details.

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
