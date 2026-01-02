#!/usr/bin/env bash
set -euo pipefail

cargo install --path .

echo "padify installed via cargo. Ensure ~/.cargo/bin is on your PATH."
