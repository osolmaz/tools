from __future__ import annotations

import io
from pathlib import Path

import cairosvg
from PIL import Image


def load_tile(source: Path) -> Image.Image:
    """Load an SVG or raster image and crop transparent outer space."""
    if not source.is_file():
        raise FileNotFoundError(source)

    if source.suffix.lower() == ".svg":
        rendered = cairosvg.svg2png(
            url=str(source),
            output_width=1600,
        )
        if not isinstance(rendered, bytes):
            raise RuntimeError("SVG renderer did not return image data")
        tile = Image.open(io.BytesIO(rendered)).convert("RGBA")
    else:
        tile = Image.open(source).convert("RGBA")

    bbox = tile.getchannel("A").getbbox()
    if bbox is None:
        raise ValueError("input image has no visible pixels")
    return tile.crop(bbox)
