#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
PROJECT_ROOT=$(cd -- "$SCRIPT_DIR/.." && pwd)
STAGED=0

cleanup() {
  if [[ "$STAGED" == 1 ]]; then
    rm -rf -- "$PROJECT_ROOT/.github"
  fi
}
trap cleanup EXIT

cd -- "$PROJECT_ROOT"
if [[ -e .github ]]; then
  echo "refusing to replace an existing response-style/.github directory" >&2
  exit 1
fi
mkdir -p .github/workflows
STAGED=1
cp ../.github/workflows/response-style.yml .github/workflows/response-style.yml
uvx slophammer-py@0.4.0 dry .
uvx slophammer-py@0.4.0 check . --execute
