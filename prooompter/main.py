"""Allows ``python main.py`` to behave like the installed CLI."""

from prooompter.cli import main


if __name__ == "__main__":  # pragma: no cover - CLI invocation helper
    raise SystemExit(main())
