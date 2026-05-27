# Codex Session Extract

Inspect a local Codex rollout JSONL file and extract every recoverable plaintext
message from normal rollout rows and compaction checkpoints.

## Extract Messages

Markdown transcript:

```bash
cargo run --bin codex-session-extract -- /path/to/rollout.jsonl
```

Markdown mode dedupes duplicate storage rows and prints role blocks similar to
the agent transcript helper. Use JSONL mode for the raw recoverable records.

Exact machine-readable records:

```bash
cargo run --bin codex-session-extract -- /path/to/rollout.jsonl --jsonl
```

Include opaque encrypted blob locations and lengths:

```bash
cargo run --bin codex-session-extract -- /path/to/rollout.jsonl --include-encrypted
```

Include injected setup messages as well as conversation messages:

```bash
cargo run --bin codex-session-extract -- /path/to/rollout.jsonl --include-setup
```

See `docs/rollout-format.md` for the observed file format and limits.
