# Codex Tools

Inspect and repair local Codex session metadata.

## Extract messages

Markdown transcript:

```bash
cargo run --bin codex-tools -- extract /path/to/rollout.jsonl
```

Markdown mode dedupes duplicate storage rows and prints role blocks similar to
the agent transcript helper. Use JSONL mode for the raw recoverable records.

Exact machine-readable records:

```bash
cargo run --bin codex-tools -- extract /path/to/rollout.jsonl --jsonl
```

Include opaque encrypted blob locations and lengths:

```bash
cargo run --bin codex-tools -- extract /path/to/rollout.jsonl --include-encrypted
```

Include injected setup messages as well as conversation messages:

```bash
cargo run --bin codex-tools -- extract /path/to/rollout.jsonl --include-setup
```

See `docs/rollout-format.md` for the observed file format and limits.

## Change session cwd

Change the stored working directory for a session:

```bash
cargo run --bin codex-tools -- set-cwd 019e8c6a-fc86-7be1-acc1-222168203f83 /Users/onur/repos/huggingclaw
```

The session argument can be a full session id, a unique session id prefix, or a
path to a rollout JSONL file. The command updates:

- `~/.codex/state_5.sqlite`, when the thread row exists.
- The session rollout JSONL metadata rows: `session_meta` and `turn_context`.
- `~/.codex/config.toml`, adding a trusted project entry for the new cwd unless
  `--no-trust-project` is passed.

Safety behavior:

- SQLite is checked with `PRAGMA integrity_check` before and after the update.
- SQLite backup uses `VACUUM INTO`, not raw file copying.
- Rollout JSONL is parsed and rewritten to a temporary file before replacement.
- Backups are created next to every modified file.

Preview a change:

```bash
cargo run --bin codex-tools -- set-cwd 019e8c6a /Users/onur/repos/huggingclaw --dry-run
```
