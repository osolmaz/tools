---
name: use-fable
description: Use when asking Claude Fable to review, research, plan, or implement work. Always invokes Claude Fable through the ACPX Cursor adapter with explicit model selection, long timeouts, suitable permissions, persistent sessions for substantial work, and local verification of the result.
---

# Use Fable

Use Claude Fable through ACPX's Cursor adapter. Never substitute another ACPX
adapter or model.

## Required Invocation

Always pass all three of these explicitly:

- `acpx`
- `--model claude-fable-5`
- `cursor`

Run from the target repository or pass `--cwd <repo>`.

For a short or ordinary task, use a 30-minute timeout:

```bash
acpx --cwd "$REPO" --timeout 1800 \
  --model claude-fable-5 \
  --approve-reads --non-interactive-permissions deny \
  cursor exec "$PROMPT"
```

For a very long task, use a 12-hour timeout and a named persistent session:

```bash
acpx --cwd "$REPO" --timeout 43200 cursor sessions ensure --name fable-work
acpx --cwd "$REPO" --timeout 43200 \
  --model claude-fable-5 \
  --approve-reads --non-interactive-permissions deny \
  cursor -s fable-work "$PROMPT"
```

Use 12 hours for deep repository audits, large implementations, long test loops,
or work where restarting would lose substantial progress. Do not use a shorter
ACPX timeout merely because the calling tool polls more frequently; keep polling
the running process until ACPX exits.

## Permissions

- For review, research, or planning, use `--approve-reads` with
  `--non-interactive-permissions deny` and tell Fable not to edit files.
- For implementation, use `--approve-all` only when the user has authorized
  delegated edits and command execution.
- ACPX permission modes are mutually exclusive.

## Working Rules

- State the task, scope, constraints, expected evidence, and output format.
- Omit low `--max-turns` limits unless the user explicitly requests one.
- For substantial work, prefer a named session so interrupted output can be
  recovered with `acpx cursor sessions history <name>`.
- Treat Fable's answer as advisory. Verify findings, edits, and tests locally
  before acting on or reporting them.
- If ACPX rejects the model identifier, inspect the model advertised by the
  Cursor adapter and select the exact Claude Fable identifier. Do not silently
  fall back to another model.
