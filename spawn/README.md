# spawn

A lightweight toolkit for orchestrating agent runs. Today it receives tasks from markdown todos, extracts unchecked items (including indented subitems), builds prompts, and spawns a tmux window per item to run your chosen harness command.

## Install

```bash
cargo install --path .
```

## Usage

General form:

```bash
spawn --file <tasks.md> run -- "<harness command with {item}>"
```

Examples:

```bash
# Codex example
spawn --file todos.md run -- "codex --model \"gpt-5.2\" -c \"model_reasoning_effort=xhigh\" -- {item}"

# Any CLI that accepts a prompt as a trailing argument
spawn --file tasks.md run -- "my-agent --temperature 0.2 -- {item}"

# You can also pass a fully split command instead of a single quoted string
spawn --file tasks.md run -- my-agent --temperature 0.2 -- {item}
```

### Required placeholder
Your harness command must include `{item}`.

The placeholder is replaced with the full todo block (including indented subitems).

## Common flags

- `--session <name>`: tmux session name (default: `spawn`)
- `--replace`: replace an existing session
- `--attach`: attach after spawning
- `--prefix "..."`: add text before each item
- `--suffix "..."`: add text after each item
- `--dry-run`: print prompts instead of launching tmux
- `--yes`: skip confirmation

## Quoting tips

If you wrap the whole harness command in double quotes, you must escape any inner double quotes:

```bash
spawn --file todos.md run -- "codex --model \"gpt-5.2\" -c \"model_reasoning_effort=xhigh\" -- {item}"
```

Use `{item}` as the placeholder in your harness command.

## Example markdown

```md
- [ ] Just say foo
  - [ ] subtask should be included
  - notes: keep this with the parent

- [x] done item should be ignored

- [ ] Just say bar
    continued detail line
    - [ ] nested unchecked item
```

## Notes

- Items are detected by unchecked markdown checkboxes (`- [ ]`, `* [ ]`, `+ [ ]`).
- Any indented lines after an unchecked item are included with that item until the indent decreases.
- The harness command is run in a new tmux window per item.
