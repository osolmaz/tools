# TileKit

TileKit turns one PNG, JPEG, WebP, or SVG image into a balanced tile pattern.
It varies tile sizes and angles, avoids visible overlap, and produces the same layout every time for a given preset.

## Install

```sh
cd tilekit
uv sync --dev
```

## Use

```sh
uv run tilekit path/to/tile.svg --output pattern.png
```

The default output is 3840×2160. Set another canvas size or layout preset when needed:

```sh
uv run tilekit tile.png \
  --width 2560 \
  --height 1440 \
  --preset denser-even \
  --output tiled.png \
  --check
```

`--check` exits with an error when the generated layout misses TileKit's spacing and balance bounds.
