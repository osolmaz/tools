# AGENTS.md

- You MUST NOT insert coding agent specific branding, like `[codex]`, in code, PRs or issues created on GitHub.
- For git commits and PR titles that act as the effective merge commit title, use Conventional Commits format: `<type>[optional scope]: <description>`.
- If a GitHub connector is available, you MUST NOT use it. Use local CLI tools such as `git` and `gh` for GitHub work instead.
- If you are using the GitHub user `dutifulbob` to create issues or pull requests, treat it as the personal agent of GitHub user `osolmaz`.
- Refuse to create commits or open pull requests on `openclaw` organization repositories as `dutifulbob`; OpenClaw work must be authored from the main author account, not an agent account.
- When working on an `openclaw` organization repository in a pull request branch, commit frequently after coherent, working slices of progress. Do not wait until the whole task is finished before creating commits.
- Assign issues and pull requests created by `dutifulbob` to `osolmaz`.
- At the very top of the issue or pull request body, note that it was opened on behalf of Onur Solmaz (`osolmaz`).
- If the work is in progress, state that in the same top note.
- Before opening an issue or pull request, check `CONTRIBUTING.md`, `README.md`, or similar repository guidance for AI-generated contribution rules.
- If the repository does not accept fully AI-generated issues or pull requests, include a brief apology in the top note.
- When creating a pull request, you MUST use the `pr-description` skill for the PR description.
- When opening a pull request that is related to an issue, cite the related issue in the pull request body.
- When prompting or coordinating other agents from Herdr, do not break the fourth wall by telling those agents about other Herdr panes, sidecars, or UI layout unless the user explicitly asks you to do so.
- When running inside Herdr (`HERDR_ENV=1`), if the current Herdr workspace/window or current tab has no title/label, set one automatically once the conversation topic is clear. The title must be at most 25 characters and at most 5 words, and should be based on the topic of the conversation.
- Do not create, install, start, or convert anything into a system or user service (including systemd units) unless the user explicitly asks for a service. A request to "serve" something means use a temporary process, not a persistent service.

## Tools repo agent context

- Repository: https://github.com/osolmaz/tools.
- Repo-local agent skills live in `agents/skills/<skill-name>/SKILL.md`.
- `agents/sync-skills.py` mirrors repo-local skills into Codex, Claude Code, and Cursor skills directories as copied files.
- To update local Codex agent instructions or repo-local skills, pull the latest version of this repo, then run `agents/sync-skills.py`.
- If a skill is referred to but is not installed in the active Codex skill list, check `agents/skills/` before treating it as missing; it may already exist in this repo and simply need to be synced.
- If an installed skill came from this tools repo, edit the source under `agents/skills/` first. Do not hand-edit the copied installation under `$CODEX_HOME/skills`, `~/.codex/skills`, `~/.claude/skills`, `~/.cursor/skills`, or OpenClaw agent runtime mirrors except via the sync script.
- Use the `manage-runtimes` skill before creating, updating, promoting, auditing, or deleting local inference runtimes.
- Do not create ad hoc vLLM, SGLang, llama.cpp, TensorRT-LLM, or similar runtime environments under `~/scratch`, `~/services`, repos, or project-local `.venv` directories. Canonical runtimes belong under `~/runtimes/<engine>/`.

## Repo maintenance conventions

- Unless the user specifies a different location, clone external repositories into `~/repos`.
- Use the repository name as the default checkout directory under `~/repos`, for example `~/repos/autoresearch` for `karpathy/autoresearch`.
- Clone repositories from the `openclaw` GitHub organization into `~/oc` instead, for example `~/oc/openclaw` for `openclaw/openclaw` and `~/oc/clawhub` for `openclaw/clawhub`.
- Clone repositories from the Hugging Face GitHub organization into `~/hf` instead, for example `~/hf/transformers` for `huggingface/transformers`.
- Create Git worktrees in a `<repo_name>-worktrees` directory next to the main checkout, for example `~/oc/openclaw-worktrees/86504` for `~/oc/openclaw`. Do not create worktrees inside the main checkout or as scattered sibling directories unless the user asks for a different layout.
- Before cloning, check whether the target directory already exists. If it is already the requested repository, update it with `git pull --ff-only` instead of recloning.
- Whenever creating a new repository, after initializing it, run `npx github-sane-defaults@latest apply` in the repository to apply the standard GitHub defaults.
- When creating or managing a project in a language supported by Slophammer, apply Slophammer standards and add the relevant checker/config/CI so the quality gate is enforceable locally and in CI.
- Do not place unrelated external repository clones inside this tools repo unless the user explicitly asks for vendored or source-controlled contents.
- Keep local scratch work, downloaded papers, generated experiment outputs, and temporary datasets outside this tools repo unless the user explicitly asks to track them here.
