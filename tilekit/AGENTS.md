# TileKit agent instructions

- Use `uv` for dependencies, environments, and commands
- Run `uv run ruff format --check .`, `uv run ruff check .`, `uv run mypy`, `uv run pytest --cov=tilekit --cov-fail-under=85`, and `scripts/check-slophammer.sh` before finishing
- Keep public functions and meaningful helpers fully typed; do not introduce `Any`
- Add or update tests for every behavior change
- Keep layout and rendering logic in `core.py`, image loading in `images.py`, and command-line IO in `cli.py`
- Prefer standard-library code over new dependencies; justify any new runtime dependency
- Follow Slophammer's agent entrypoint when changing quality policy: <https://github.com/osolmaz/slophammer/blob/main/docs/AGENT_ENTRYPOINT.md>
