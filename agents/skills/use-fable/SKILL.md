---
name: use-fable
description: Use only when the human explicitly asks to call or use Claude Fable for review, research, planning, or implementation. Fable is very expensive to run, so use it sparingly even when authorized. Invoke it through the local Claude Code CLI via ACPX's Claude adapter, never through Cursor, with explicit model selection, long timeouts, suitable permissions, persistent sessions for substantial work, and local verification.
---

# Use Fable

Use this skill only when the human explicitly asks to call or use Claude Fable.
Do not infer permission from the task type, difficulty, quality bar, failed local
attempts, available budget, or potential usefulness. If the human did not
explicitly request Fable, do not invoke it; continue the work yourself or ask
first.

Fable is very expensive to run. Use it sparingly in general, including when the
human has authorized it. Keep the scope and number of calls no larger than the
request requires. Never launch parallel Fable calls unless the human explicitly
asks for parallel calls.

Run Fable through the locally installed Claude Code CLI using ACPX's `claude`
adapter. Never use the Cursor adapter for Fable and never substitute another
adapter or model.

## Required Invocation

Always pass all three of these explicitly:

- `acpx`
- `--model claude-fable-5`
- `claude`

Run from the target repository or pass `--cwd <repo>`.

For a short or ordinary task, use a 30-minute timeout:

```bash
acpx --cwd "$REPO" --timeout 1800 \
  --model claude-fable-5 \
  --approve-reads --non-interactive-permissions deny \
  claude exec "$PROMPT"
```

For a very long task, use a 12-hour timeout and a named persistent session:

```bash
acpx --cwd "$REPO" --timeout 43200 claude sessions ensure --name fable-work
acpx --cwd "$REPO" --timeout 43200 \
  --model claude-fable-5 \
  --approve-reads --non-interactive-permissions deny \
  claude -s fable-work "$PROMPT"
```

Use 12 hours for deep repository audits, large implementations, long test loops,
or work where restarting would lose substantial progress. Do not use a shorter
ACPX timeout merely because the calling tool polls more frequently; keep polling
the running process until ACPX exits.

## Permissions

- For review, research, or planning, use `--approve-reads` with
  `--non-interactive-permissions deny` and tell Fable not to edit files.
- For implementation, use `--approve-all` only when the human explicitly
  authorized Fable to make delegated edits and execute commands.
- ACPX permission modes are mutually exclusive.

## Working Rules

- Reconfirm that the human explicitly requested Fable before every new session
  or additional call.
- State the task, scope, constraints, expected evidence, and output format.
- Omit low `--max-turns` limits unless the human explicitly requests one.
- For substantial work, prefer a named session so interrupted output can be
  recovered with `acpx claude sessions history <name>`.
- Treat Fable's answer as advisory. Verify findings, edits, and tests locally
  before acting on or reporting them.
- If ACPX rejects the model identifier, inspect the model advertised by the
  local Claude adapter and select the exact Claude Fable identifier. Do not
  silently fall back to another model or to Cursor.
