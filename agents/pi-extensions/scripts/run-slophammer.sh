#!/bin/sh
set -eu

workflow=".github/workflows/pi-extensions.yml"
cleanup() {
  rm -f "$workflow"
  rmdir .github/workflows .github 2>/dev/null || true
}
stage_workflow() {
  mkdir -p .github/workflows
  sed \
    -e 's#agents/pi-extensions/packages/#packages/#g' \
    -e 's#working-directory: agents/pi-extensions#working-directory: .#g' \
    ../../.github/workflows/pi-extensions.yml >"$workflow"
}

if [ "${1:-}" = "--stage-only" ]; then
  stage_workflow
  exit 0
fi

trap cleanup EXIT HUP INT TERM
stage_workflow
slophammer-ts check . --execute
