# prooompter

![e260f1ab116c447372c9d977e10ccdba](https://github.com/user-attachments/assets/3af86655-c49b-4537-879d-798b7869c714)

A CLI for extracting repository context into prompt-friendly text chunks. The codebase
is adapted from [files-to-prompt](https://github.com/simonw/files-to-prompt) and
packaged for repeatable installs via [uv](https://docs.astral.sh/uv/).

## Development quickstart

1. Install dependencies with `uv sync` (or `uv pip install -e .` for editable mode).
2. Run the tool from source via `uv run prooompter --help`.
3. Format or lint using your preferred tools before submitting changes.

## Configuration

Optional CLI defaults can be stored in `prooompter.toml` at the repository root. See
`src/prooompter/cli.py` for supported keys such as `[ignore]` and `ignore.paths`.

## Packaging notes

The project follows the `src/` layout recommended for uv-based libraries. The
`pyproject.toml` declares the CLI entry point under `[project.scripts]` so installs
expose a `prooompter` command automatically.
