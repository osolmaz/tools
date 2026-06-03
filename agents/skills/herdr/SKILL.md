---
name: herdr
description: Use when running inside Herdr to inspect and control Herdr workspaces, tabs, panes, agents, output waits, sibling terminal processes, and GitHub PR sidecar layouts through the herdr CLI.
---

# Herdr

Use this skill only when `HERDR_ENV=1`. If that variable is not set to `1`,
state that the current process is not running inside a Herdr-managed pane and do
not control the focused Herdr pane.

Herdr is a terminal workspace manager. Its CLI talks to the running Herdr
instance over the local socket and can manage workspaces, tabs, panes, agents,
and waits.

## Core Rules

- Re-read IDs before acting. Workspace, tab, and pane IDs can change when panes,
  tabs, or workspaces close.
- Do not guess IDs from old context. Use `herdr workspace list`, `herdr tab
  list`, `herdr pane list`, or the JSON returned by create/split commands.
- Use `--no-focus` when creating tabs, workspaces, or splits unless the user
  explicitly wants focus moved.
- Use `pane read` for output that already exists.
- Use `wait output` or `wait agent-status` for future state changes.
- After spawning or prompting an agent in a pane, do not wait for the agent to
  finish unless the user explicitly asks you to wait for completion or collect
  the final answer. It is enough to verify the command or prompt landed and the
  agent started working.
- Parse JSON from create/split commands instead of hard-coding returned IDs.

## Discovery

Check the current panes and focused pane:

```bash
herdr pane list
```

List workspaces:

```bash
herdr workspace list
```

List tabs in a workspace:

```bash
herdr tab list --workspace 1
```

## Reading Panes

Read recent pane output:

```bash
herdr pane read 1-1 --source recent --lines 50
```

Useful sources:

- `visible`: current viewport.
- `recent`: recent scrollback as rendered.
- `recent-unwrapped`: recent terminal text with soft wraps joined. This matches
  how `wait output --source recent` searches text.

Use ANSI output when visual terminal state matters:

```bash
herdr pane read 1-1 --source recent --format ansi --lines 50
```

## Running Commands In Panes

Split the current pane and keep focus:

```bash
NEW_PANE=$(herdr pane split 1-2 --direction right --no-focus | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane run "$NEW_PANE" "npm run dev"
```

Split directions are `right` and `down`:

```bash
herdr pane split 1-2 --direction down --no-focus
```

Send text without Enter:

```bash
herdr pane send-text 1-1 "hello"
```

Send keys:

```bash
herdr pane send-keys 1-1 Enter
```

Run command text plus Enter:

```bash
herdr pane run 1-1 "echo hello"
```

## Waiting

Wait for output:

```bash
herdr wait output 1-3 --match "ready" --timeout 30000
```

Use regex matching when needed:

```bash
herdr wait output 1-3 --match "server.*ready" --regex --timeout 30000
```

Wait for another agent:

```bash
herdr wait agent-status 1-1 --status done --timeout 60000
```

Agent statuses are `idle`, `working`, `blocked`, `done`, and `unknown`.

## Workspace And Tab Management

Create a workspace:

```bash
herdr workspace create --cwd /path/to/project --label "api server" --no-focus
```

Focus, rename, or close a workspace:

```bash
herdr workspace focus 2
herdr workspace rename 2 "api server"
herdr workspace close 2
```

Create, focus, rename, or close a tab:

```bash
herdr tab create --workspace 1 --label "logs" --no-focus
herdr tab focus 1:2
herdr tab rename 1:2 "logs"
herdr tab close 1:2
```

## PR Management

When the user asks to use Herdr to open a GitHub PR, always build a two-pane
view:

- Left pane: `ghzinga`/`gzg` showing the PR.
- Right pane: Codex running from the relevant repo or a PR-specific worktree.

Prefer a dedicated worktree for the right pane when the task may involve code
review, edits, tests, CI repair, or follow-up implementation. Reuse an existing
matching worktree if one already exists; otherwise create one using the repo's
normal worktree conventions before launching Codex.

Quote GitHub resources that contain `#` so shells do not treat the number as a
comment or pattern:

```bash
gzg 'owner/repo#123'
```

Recipe:

```bash
WORKTREE=/path/to/repo-worktrees/pr-123
WORKSPACE=$(herdr workspace create --cwd "$WORKTREE" --label "repo PR #123" --focus | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["workspace"]["workspace_id"])')
LEFT=$(herdr pane list | python3 -c 'import json,sys; data=json.load(sys.stdin)["result"]["panes"]; print(next(p["pane_id"] for p in data if p["workspace_id"] == "'$WORKSPACE'" and p.get("focused")))')
RIGHT=$(herdr pane split "$LEFT" --direction right --cwd "$WORKTREE" --no-focus | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane rename "$LEFT" "PR #123"
herdr pane rename "$RIGHT" "codex PR #123"
herdr pane run "$LEFT" "gzg 'owner/repo#123'"
herdr pane run "$RIGHT" "codex"
```

After launch, read both panes to verify the left pane is rendering the PR and
the right pane is an idle Codex session in the intended worktree.

## Recipes

Run a server in a sibling pane and wait for readiness:

```bash
NEW_PANE=$(herdr pane split 1-2 --direction right --no-focus | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane run "$NEW_PANE" "npm run dev"
herdr wait output "$NEW_PANE" --match "ready" --timeout 30000
herdr pane read "$NEW_PANE" --source recent --lines 20
```

Run tests in a sibling pane:

```bash
NEW_PANE=$(herdr pane split 1-2 --direction down --no-focus | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane run "$NEW_PANE" "cargo test"
herdr wait output "$NEW_PANE" --match "test result" --timeout 60000
herdr pane read "$NEW_PANE" --source recent --lines 30
```

Inspect another agent:

```bash
herdr pane list
herdr pane read 1-1 --source recent --lines 80
```

Coordinate with another agent:

```bash
herdr wait agent-status 1-1 --status done --timeout 120000
herdr pane read 1-1 --source recent --lines 100
```

Spawn another agent:

```bash
NEW_PANE=$(herdr pane split 1-2 --direction right --no-focus | python3 -c 'import json,sys; print(json.load(sys.stdin)["result"]["pane"]["pane_id"])')
herdr pane run "$NEW_PANE" "codex"
herdr wait output "$NEW_PANE" --match ">" --timeout 15000
herdr pane run "$NEW_PANE" "review the test coverage in src/api/"
```

## Output Notes

- `workspace list`, `workspace create`, `tab list`, `tab create`, `tab get`,
  `tab focus`, `tab rename`, `tab close`, `pane list`, `pane get`, `pane split`,
  `wait output`, and `wait agent-status` print JSON on success.
- `pane read` prints text.
- `pane send-text`, `pane send-keys`, and `pane run` print nothing on success.
- `workspace create` returns `result.workspace`, `result.tab`, and
  `result.root_pane`.
- `tab create` returns `result.tab` and `result.root_pane`.
- `pane split` returns the new pane ID at `result.pane.pane_id`.
