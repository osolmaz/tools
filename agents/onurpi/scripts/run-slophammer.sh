#!/bin/sh
set -eu

workflow=".github/workflows/onurpi.yml"
cleanup() {
  rm -f "$workflow"
  rmdir .github/workflows .github 2>/dev/null || true
}
stage_workflow() {
  mkdir -p .github/workflows
  sed \
    -e 's#agents/onurpi/packages/#packages/#g' \
    -e 's#working-directory: agents/onurpi#working-directory: .#g' \
    ../../.github/workflows/onurpi.yml >"$workflow"
}

if [ "${1:-}" = "--stage-only" ]; then
  stage_workflow
  exit 0
fi

trap cleanup EXIT HUP INT TERM
stage_workflow
slophammer-ts check . --execute
