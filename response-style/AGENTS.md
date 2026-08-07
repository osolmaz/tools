# Response Style agent instructions

- Use `uv` for dependencies, environments, and commands.
- Keep generated datasets outside Git. Never print example text in commands, tests, logs, pull requests, or issues.
- Read only explicitly supplied conversation roots. Do not add network access or credential discovery.
- Keep source adapters strict. Record unsupported data as bounded issues instead of guessing.
- Use only visible user and assistant text. Exclude reasoning, tool calls, tool results, system prompts, and subagent prompts.
- Use standard-library runtime dependencies unless the user approves another dependency.
- Keep public functions and meaningful helpers fully typed. Do not introduce `Any`.
- Add or update synthetic tests for every behavior change.
- Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, `uv run pytest --cov=response_style --cov-fail-under=85`, `uv run pip-audit`, and `scripts/check-slophammer.sh` before finishing.
- Follow Slophammer's agent entrypoint when changing quality policy: <https://github.com/osolmaz/slophammer/blob/main/docs/AGENT_ENTRYPOINT.md>.
