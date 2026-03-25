# acpx

This directory holds agent-facing assets for `acpx` workflows.

Structure:

- `workflows/` — executable flow modules
- `prompts/` — prompt text used by those workflows
- `lib/` — small helper scripts for running flows and gathering context
- `test/` — local tests for the lightweight helper/runtime code

## Run a flow

From the repo root:

```bash
node agents/acpx/run-flow.js run agents/acpx/workflows/echo.flow.js \
  --acpx /Users/onur/offline/acpx/dist/cli.js \
  --acpx-cwd /Users/onur/offline/acpx \
  --agent codex \
  --input-json '{"request":"Summarize this repository in one sentence."}'
```

## Included workflows

- `workflows/echo.flow.js` — one ACP step that returns JSON
- `workflows/branch.flow.js` — ACP classification followed by a local branch
- `workflows/two-turn.flow.js` — two ACP prompts in one persistent session
- `workflows/pr-triage.flow.js` — full maintainability-first PR triage flow with GitHub context

## Notes

- The helper runner shells out to `acpx`; it is not a separate package.
- `prompts/` stores the reusable prompt text so workflows stay mostly wiring and routing code.
- `lib/github.js` is only for the PR triage workflow and lives here because it is workload-specific helper code, not core `acpx` logic.
