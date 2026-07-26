# AGENTS.md

- You MUST NOT insert coding agent specific branding, like `[codex]`, in code, PRs or issues created on GitHub.
- For git commits and PR titles that act as the effective merge commit title, use Conventional Commits format: `<type>[optional scope]: <description>`.
- If a GitHub connector is available, you MUST NOT use it. Use local CLI tools such as `git` and `gh` for GitHub work instead.
- When asked for a GitHub link to a file, use the relevant branch name in the URL rather than a commit SHA.
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
- Do not run Codex review for documentation-only changes.
- When asked to review, perform the review yourself. Do not delegate, defer, or ask another agent to review unless the human explicitly instructs you to call another agent for that review.
- When a pull request is documentation-only or similarly trivial, relevant local checks such as SimpleDoc provide enough confidence, and the user has authorized merging, merge it opportunistically without waiting for CI/CD.
- This workflow guidance does not grant merge authorization. Do not merge a pull request unless the user explicitly requested it or provided an applicable standing instruction to merge.
- When prompting or coordinating other agents from Herdr, do not break the fourth wall by telling those agents about other Herdr panes, sidecars, or UI layout unless the user explicitly asks you to do so.
- When running inside Herdr (`HERDR_ENV=1`), if the current Herdr workspace/window or current tab has no title/label, set one automatically once the conversation topic is clear. The title must be at most 25 characters and at most 5 words, and should be based on the topic of the conversation.
- Do not create, install, start, or convert anything into a system or user service (including systemd units) unless the user explicitly asks for a service. A request to "serve" something means use a temporary process, not a persistent service.

## Consequential comparison policy

- Use the `practical-significance` skill before a measured difference determines spending, scaling, shipping, architecture, or operational complexity.
- Report the absolute effect and raw counts, then account for uncertainty and compare the result with a minimum worthwhile effect.
- Treat uncertain or immaterial differences as ties. Prefer the cheaper, faster, simpler, safer option unless the user explicitly chooses another tradeoff.
- Do not let an automatic metric winner or `argmax` cross a spending or shipping boundary.
- Never promote a diagnostic, ablation, search, or report-only checkpoint to production from a metric lead alone. Check its registered role, practical significance, downstream dependencies, and selection authority first.
- Keep observed, recommended, and explicitly approved model states separate. If a plan requires maintainer approval, only a direct selection of the named candidate marks it approved.
- Before changing the production model, list the pilots, probes, generated data, exports, benchmarks, and cost estimates tied to the incumbent and state what must be repeated.
- Describe a held-out regression as consistent with overfitting unless paired errors, learning curves, repeated runs, or another registered test establish the cause.

## Paid compute policy

- Use the `paid-compute-launch` skill before launching, scaling, retrying, or automatically continuing paid accelerator work.
- A substantial launch requires measured throughput, a low and high cost estimate, cheaper hardware or reuse alternatives, a cost ceiling, and explicit approval after those facts are presented.
- A long output-producing Job must publish durable partial outputs and pass a real pause-resume canary. Logs and progress counters do not count as saved work.
- When one Job reveals a deterministic defect in shared worker code or data assumptions, pause the affected fleet at safe boundaries before retrying. Do not leave sibling Jobs running known-vulnerable code.
- Verify historical runtime claims from source Job records. State every mismatch in model, decoding, batch size, hardware, row count, or input distribution.
- Stop automatic continuation whenever observed cost, method, hardware, failure state, or checkpoint-reuse assumptions differ from what the user approved.

## Cutover policy

- Default to a hard cutover. Do not add or retain legacy shims, compatibility aliases, fallback readers, dual-read or dual-write paths, transitional adapters, or indefinite deprecation paths unless the repository is covered by an exception below or the user explicitly requests compatibility.
- Use `cutover` only to describe replacement behavior in prose. Do not use `cutover` or `cutover plan` in filenames, document titles, headings, plan names, issue titles, pull request titles, commit subjects, test names, or other identifiers. Name the target capability directly, adding `implementation plan` only when a plan suffix is useful.
- For repositories owned by `osolmaz`, always replace the existing contract in place and remove the superseded path. Do not introduce a parallel `v2` or similar version solely to preserve old behavior; keep the existing version identifier, such as `v1`, and change it in place. This remains the rule until the repository is explicitly added to the exception list.
- A deprecation period in an owned repository must be bounded and end in removal. It must not leave runtime compatibility code after the cutover.
- Exception list:
  - `openclaw/*`.
  - Important repositories not owned by `osolmaz`; follow upstream compatibility and maintainer requirements.
- A repository owned by `osolmaz` is not exempt merely because it is important. Add an owned repository to the exception list only when the user explicitly says so.
- Explicit user instructions for a task override this default.

## Tools repo agent context

- Repository: https://github.com/osolmaz/tools.
- Repo-local agent skills live in `agents/skills/<skill-name>/SKILL.md`.
- `agents/sync-skills.py` mirrors repo-local skills into Codex, Claude Code, Cursor, and Pi skills directories as copied files.
- To update local agent instructions or repo-local skills, pull the latest version of this repo, then run `agents/sync-skills.py`.
- Use the `pi-coding-agent` skill for any task involving Pi, including its extensions, packages, skills, themes, TUI, SDK, models, providers, configuration, or local state.
- Use the `extending-pi` skill alongside `pi-coding-agent` before proposing, designing, implementing, reviewing, or debugging any change to Pi behavior. This includes deciding between an extension and Pi core, and requests for elegant, long-term, production-ready, ideal, or holy-grail Pi solutions.
- If a skill is referred to but is not installed in the active Codex skill list, check `agents/skills/` before treating it as missing; it may already exist in this repo and simply need to be synced.
- If an installed skill came from this tools repo, edit the source under `agents/skills/` first. Do not hand-edit the copied installation under `$CODEX_HOME/skills`, `~/.codex/skills`, `~/.claude/skills`, `~/.cursor/skills`, `~/.pi/agent/skills`, or OpenClaw agent runtime mirrors except via the sync script.
- Use the `manage-runtimes` skill before creating, updating, promoting, auditing, or deleting local inference runtimes.
- Do not create ad hoc vLLM, SGLang, llama.cpp, TensorRT-LLM, or similar runtime environments under `~/scratch`, `~/services`, repos, or project-local `.venv` directories. Canonical runtimes belong under `~/runtimes/<engine>/`.

## Credential handling policy

- Never copy a credential from one store to another — local token files, agent
  configs, Space or repo secrets, CI variables, `.env` files, other machines —
  without the user's explicit approval for that specific copy, naming the
  source and the destination.
- Using a locally configured credential in place for its normal purpose
  (`gh`/`hf` CLI calls, git pushes over existing auth) is fine; persisting it
  anywhere new is not.
- When a service needs a credential, ask which one to use. Prefer
  purpose-scoped tokens over broad account tokens.
- Never print secret values into logs, chat output, commits, or files. Use
  masked previews (first/last characters) when identification is needed.
- If a credential was persisted somewhere without approval, disclose it
  immediately, overwrite or remove it, and recommend rotating the exposed
  credential.

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
