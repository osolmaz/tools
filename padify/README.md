# padify

Add padding to images (handy for terminal screenshots).

## Usage

```bash
padify input.png
padify input.png output.png --pad 120
padify input.png --pad-x 120
padify input.jpg --all 64 --bg "#0b0f14"
padify input.png --bg transparent
padify input.png --no-crop
padify input.png --debug-crop
```

Defaults:
- padding = auto (same value for both directions, based on image size)
- `--bg` = `auto` (deduced from the image)
- output path = `<input>_pad.<ext>`

Notes:
- Supports common image formats (png, jpg, etc.).
- Automatically trims partial bottom artifacts (like a cut-off last line or cursor).
- Video/recording padding isn't supported yet.

## Install

```bash
./install.sh
```
