#!/usr/bin/env bash
set -euo pipefail

if [[ -e .github ]]; then
  echo "tilekit/.github already exists; refusing to replace it" >&2
  exit 2
fi

mkdir -p .github/workflows
trap 'rm -rf .github' EXIT
cp ../.github/workflows/tilekit.yml .github/workflows/tilekit.yml

uvx slophammer-py@0.4.0 check . --execute
