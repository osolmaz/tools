# Codex Rollout JSONL Format Notes

Codex stores local session rollout data as newline-delimited JSON. Each line is a
JSON object with:

- `timestamp`: when the rollout record was written.
- `type`: the top-level rollout record kind.
- `payload`: the record body.

## Top-Level Kinds Observed

- `session_meta`: session identity, working directory, model/provider metadata, and injected instruction context.
- `turn_context`: per-turn runtime context such as cwd, model, sandbox, and tool surface.
- `event_msg`: user-visible app events. `event_msg.user_message` and `event_msg.agent_message` contain plaintext transcript text in `payload.message`.
- `response_item`: model replay items. `response_item` with `payload.type == "message"` contains role-tagged plaintext content in `payload.content`.
- `compacted`: compaction checkpoint. Newer Codex versions can persist `payload.replacement_history`, a list of response items that replace older replay history during resume.

## Plaintext Message Locations

Recoverable plaintext conversation messages may appear in multiple places:

- `event_msg.payload.message`
- `response_item.payload.content[].text`
- `compacted.payload.replacement_history[].content[].text`

The same message can appear more than once because Codex stores both user-visible events and model replay items. Compaction can also copy later replay history into a checkpoint.

## Encrypted Content

Some records contain `encrypted_content`. The helper reports where those blobs occur and their character lengths, but it does not decrypt them. Current Codex client source treats these values as opaque model/API state.

If a user-visible message is only represented inside `encrypted_content`, this file is not enough to recover that plaintext locally.

## Resume Semantics

Codex resume does not simply replay every line from the top. The current source scans backward, finds the newest surviving compaction checkpoint with `replacement_history`, uses that as the base history, then replays the newer suffix.

That means a transcript tool needs to decide which view it wants:

- Raw recoverable ledger: every plaintext message found anywhere in the JSONL.
- Effective replay history: the newest surviving `replacement_history` plus newer replay items, with rollback semantics applied.
- Desktop visible transcript: what the app renders, which may include app-specific filtering or hydrated state outside this plaintext JSONL.

The `codex-session-extract` helper implements the raw recoverable ledger view,
with setup messages hidden by default so the first printed conversation message
usually matches the Desktop-visible session. Pass `--include-setup` to include
injected developer, environment, and AGENTS.md setup messages too.
