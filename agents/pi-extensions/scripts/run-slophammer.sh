#!/bin/sh
set -eu

workflow=".github/workflows/pi-extensions.yml"
cleanup() {
  rm -f "$workflow"
  rmdir .github/workflows .github 2>/dev/null || true
}
trap cleanup EXIT HUP INT TERM

mkdir -p .github/workflows
sed \
  -e 's#agents/pi-extensions/packages/#packages/#g' \
  -e 's#working-directory: agents/pi-extensions#working-directory: .#g' \
  ../../.github/workflows/pi-extensions.yml >"$workflow"
slophammer-ts check . --execute
