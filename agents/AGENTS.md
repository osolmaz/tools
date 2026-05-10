# AGENTS.md

- You MUST NOT insert coding agent specific branding, like `[codex]`, in code, PRs or issues created on GitHub.
- For git commits and PR titles that act as the effective merge commit title, use Conventional Commits format: `<type>[optional scope]: <description>`.
- When creating a pull request, you MUST use the `pr-description` skill for the PR description.

## Tools repo agent context

- Repository: https://github.com/osolmaz/tools.
- Repo-local agent skills live in `agents/skills/<skill-name>/SKILL.md`.
- `agents/sync-skills.py` mirrors repo-local skills into `$CODEX_HOME/skills` or `~/.codex/skills` as copied files.
- If a skill is referred to but is not installed in the active Codex skill list, check `agents/skills/` before treating it as missing; it may already exist in this repo and simply need to be synced.
