from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from tilekit.core import PRESETS, REFERENCE_HEIGHT, REFERENCE_WIDTH, CanvasSize, render_tiles
from tilekit.images import load_tile


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Scatter one or more images into a balanced, non-overlapping tile pattern."
    )
    parser.add_argument(
        "sources",
        nargs="+",
        type=Path,
        help="PNG, JPEG, WebP, or SVG tile images",
    )
    parser.add_argument("--preset", choices=sorted(PRESETS), default="denser-even")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--width", type=int, default=REFERENCE_WIDTH)
    parser.add_argument("--height", type=int, default=REFERENCE_HEIGHT)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if spatial metrics miss their bounds",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    args = build_parser().parse_args(argv)
    sources = [Path(source) for source in args.sources]
    first_source = sources[0]
    output = (
        Path(args.output)
        if args.output
        else first_source.with_name(f"{first_source.stem}-tiled.png")
    )
    canvas_size = CanvasSize(width=args.width, height=args.height)
    result = render_tiles(
        [load_tile(source) for source in sources],
        PRESETS[args.preset],
        canvas_size,
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    result.image.convert("RGB").save(output, quality=96)

    print(f"preset: {args.preset}")
    print(f"placed: {result.placed_count} of {result.prepared_count}")
    print("source_counts: " + json.dumps(result.source_counts))
    print("metrics: " + json.dumps(result.metrics, sort_keys=True))
    if result.failures:
        print("metric_failures: " + ", ".join(result.failures))
    print(f"MEDIA: {output.resolve()}")
    if args.check and result.failures:
        raise SystemExit(1)
