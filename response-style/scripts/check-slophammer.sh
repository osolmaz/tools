#!/usr/bin/env bash
set -euo pipefail

cleanup() {
  rm -rf .github
}
trap cleanup EXIT

mkdir -p .github/workflows
cp ../.github/workflows/response-style.yml .github/workflows/response-style.yml
uvx slophammer-py@0.4.0 dry .
uvx slophammer-py@0.4.0 check . --execute
