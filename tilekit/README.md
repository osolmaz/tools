# TileKit

TileKit turns one or more PNG, JPEG, WebP, or SVG images into a balanced tile pattern.
It varies tile sizes and angles, avoids visible overlap, and produces the same layout every time for a given preset. When given multiple images, TileKit represents them equally and mixes them across neighboring tiles and canvas regions.

## Install

```sh
cd tilekit
uv sync --dev
```

## Use

```sh
uv run tilekit path/to/tile.svg --output pattern.png
```

Pass multiple images to create an evenly mixed pattern:

```sh
uv run tilekit hugging-face.svg openclaw.svg --output mixed-pattern.png
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
