# PNGScrub

PNGScrub inspects PNG container metadata and writes sanitized copies without
changing the compressed image data.

It removes known provenance and privacy chunks:

- C2PA/JUMBF (`caBX`)
- EXIF (`eXIf`)
- textual metadata (`iTXt`, `tEXt`, `zTXt`)
- modification time (`tIME`)

The original file is never overwritten. Color, transparency, resolution, and
other rendering-related chunks remain intact.

## Usage

```sh
cargo run --manifest-path ~/repos/tools/pngscrub/Cargo.toml -- inspect image.png
cargo run --manifest-path ~/repos/tools/pngscrub/Cargo.toml -- clean image.png
```

Use `--aggressive` to remove unknown ancillary chunks while retaining known
rendering-related chunks:

```sh
cargo run --manifest-path ~/repos/tools/pngscrub/Cargo.toml -- clean image.png --aggressive
```

Use `--json` for machine-readable output. Use `-o` to choose the destination
and `--force` to replace an existing destination.

PNGScrub only handles PNG container metadata. It does not detect or remove
pixel-level signals such as SynthID.

