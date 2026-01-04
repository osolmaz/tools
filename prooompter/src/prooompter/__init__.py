"""Core package for the prooompter CLI."""

from __future__ import annotations

from importlib import metadata

from .cli import main

__all__ = ["main", "__version__"]

try:  # pragma: no cover - metadata not available until installed
    __version__ = metadata.version("prooompter")
except metadata.PackageNotFoundError:  # pragma: no cover - local dev fallback
    __version__ = "0.0.0"
