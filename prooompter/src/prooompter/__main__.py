"""Entry point for ``python -m prooompter``."""

from __future__ import annotations

from .cli import main


def _run() -> int:
    return main()


if __name__ == "__main__":  # pragma: no cover - CLI invocation hook
    raise SystemExit(_run())
