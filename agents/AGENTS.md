# AGENTS.md

- You MUST NOT insert coding agent specific branding, like `[codex]`, in code, PRs or issues created on GitHub.
- For git commits and PR titles that act as the effective merge commit title, use Conventional Commits format: `<type>[optional scope]: <description>`.
- If a GitHub connector is available, you MUST NOT use it. Use local CLI tools such as `git` and `gh` for GitHub work instead.
- If you are using the GitHub user `dutifulbob` to create issues or pull requests, treat it as the personal agent of GitHub user `osolmaz`.
- Assign issues and pull requests created by `dutifulbob` to `osolmaz`.
- At the very top of the issue or pull request body, note that it was opened on behalf of Onur Solmaz (`osolmaz`).
- If the work is in progress, state that in the same top note.
- Before opening an issue or pull request, check `CONTRIBUTING.md`, `README.md`, or similar repository guidance for AI-generated contribution rules.
- If the repository does not accept fully AI-generated issues or pull requests, include a brief apology in the top note.
- When creating a pull request, you MUST use the `pr-description` skill for the PR description.
- When opening a pull request that is related to an issue, cite the related issue in the pull request body.

## Tools repo agent context

- Repository: https://github.com/osolmaz/tools.
- Repo-local agent skills live in `agents/skills/<skill-name>/SKILL.md`.
- `agents/sync-skills.py` mirrors repo-local skills into `$CODEX_HOME/skills` or `~/.codex/skills` as copied files.
- To update local Codex agent instructions or repo-local skills, pull the latest version of this repo, then run `agents/sync-skills.py`.
- If a skill is referred to but is not installed in the active Codex skill list, check `agents/skills/` before treating it as missing; it may already exist in this repo and simply need to be synced.

## Repo maintenance conventions

- Unless the user specifies a different location, clone external repositories into `~/repos`.
- Use the repository name as the default checkout directory under `~/repos`, for example `~/repos/autoresearch` for `karpathy/autoresearch`.
- Clone repositories from the `openclaw` GitHub organization into `~/oc` instead, for example `~/oc/openclaw` for `openclaw/openclaw` and `~/oc/clawhub` for `openclaw/clawhub`.
- Clone repositories from the Hugging Face GitHub organization into `~/hf` instead, for example `~/hf/transformers` for `huggingface/transformers`.
- Before cloning, check whether the target directory already exists. If it is already the requested repository, update it with `git pull --ff-only` instead of recloning.
- Do not place unrelated external repository clones inside this tools repo unless the user explicitly asks for vendored or source-controlled contents.
- Keep local scratch work, downloaded papers, generated experiment outputs, and temporary datasets outside this tools repo unless the user explicitly asks to track them here.
