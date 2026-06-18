---
name: pi-demo-grid
description: Use when launching a tmux grid of concurrent localpi Pi demo sessions for live demonstrations, load demos, screen-filling demo walls, or side-by-side model output comparisons. Triggers include requests to demo localpi, open many Pi demo panes, launch concurrent demo requests, create a tmux demo grid, or run localpi --demo at a target concurrency.
---

# Pi Demo Grid

## Overview

Launch a balanced tmux session containing many concurrent `localpi --demo` panes.
Use the bundled script so pane creation, layout, and final attach instructions are deterministic.

## Workflow

1. Resolve the target concurrency.
   - If the user gives a number, use it.
   - If no number is given, ask for the target concurrency before launching.
   - Concurrency must be a positive integer.

2. Resolve the localpi demo command.
   - Prefer an explicit command when the user provides one.
   - Otherwise build `localpi --demo` plus any user-provided localpi flags.
   - Demo mode requires a concrete model. Make sure the command has `--model <id>` or `LOCALPI_MODEL` is set.

3. Launch the grid with `scripts/launch_pi_demo_grid.py`.
   - Use one tmux session per demo run.
   - Use `--restart` only when the user agrees to replace an existing session name.
   - The script applies tmux's `tiled` layout, which balances panes into equal sizes and naturally gives square layouts such as 2x2 for 4 and 4x4 for 16.

4. Report the final attach command exactly.
   - The user should be able to copy one command to view the session.
   - Also mention the session name and pane count.

## Commands

Launch 4 panes using the default `localpi --demo` command and an explicit model:

```bash
python3 agents/skills/pi-demo-grid/scripts/launch_pi_demo_grid.py \
  --concurrency 4 \
  -- localpi --demo --model gemma-e4b
```

Launch 16 panes with a named session:

```bash
python3 agents/skills/pi-demo-grid/scripts/launch_pi_demo_grid.py \
  --concurrency 16 \
  --session localpi-demo-16 \
  -- localpi --demo --model vllm/gemma4-26b
```

Use `--dry-run` first when checking the layout or command shape:

```bash
python3 agents/skills/pi-demo-grid/scripts/launch_pi_demo_grid.py \
  --concurrency 6 \
  --dry-run \
  -- localpi --demo --model gemma-e4b
```

## Script Contract

The script:

- verifies `tmux` exists before launching
- refuses to reuse an existing tmux session unless `--restart` is passed
- creates all panes in one window
- runs one command per pane with `LOCALPI_DEMO_INDEX` and `LOCALPI_DEMO_TOTAL` set
- applies `tmux select-layout tiled` after each split and at the end
- sets tmux window options that keep panes visible and stable for demos
- prints `tmux attach -t <session>` as the final user-facing command

## Notes

- Do not use background one-shot localpi commands for this skill; the purpose is a live visible tmux wall.
- Do not attach automatically unless the user asks. Create the session and report the attach command.
- If a model server cannot safely handle the requested concurrency, warn before launching but still follow the user's explicit concurrency if they confirm.
