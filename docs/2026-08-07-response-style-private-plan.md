---
title: Mine the private response-style dataset
author: Onur Solmaz <2453968+osolmaz@users.noreply.github.com>
date: 2026-08-07
---

# Mine the private response-style dataset

The `response-style-private` dataset will collect examples of Onur asking an assistant to rewrite a response with `amk` or `plain`. It will also collect long responses that received no style-revision request. The data may contain private text, source paths, or secrets printed in a conversation, so it must stay on this machine until Onur reviews it and chooses to publish a sanitized export.

## Implementation status

The CLI, all four source adapters, deterministic miner, private writer, and verifier are implemented. The test suite and CI job cover the new package. A full local run read every accessible source, wrote the private dataset under `~/.local/share/response-style-private`, and passed `verify`. Two consecutive runs produced the same example count, byte count, and SHA-256 digest while the active Pi session continued to append tool records.

The generated dataset remains outside Git. Commands and validation logs reported only counts and hashes, plus issue codes and lengths.

## Requirements

- Read existing Pi, Codex, Claude Code, and Cursor conversation stores without changing them.
- Process only explicitly supplied source roots.
- Keep visible user and assistant text. Exclude system and developer messages, reasoning, tool calls, tool results, and known injected notifications.
- Follow native conversation branches where the source records them.
- Match `amk` and `plain` as complete, case-insensitive words in a user-authored message.
- Keep the response before that message, the message itself, and the following response.
- Keep long responses when the next user message has no known style-revision signal. Keep terminal responses as a separate `conversation_ended` case.
- Record observed facts separately from the `no_revision_requested` acceptance proxy.
- Write the dataset atomically under a private directory. Create directories with mode `0700` and files with mode `0600`. Reject output inside a Git worktree.
- Never use the network, agent credentials, provider payloads, or a model classifier.
- Never print conversation text from `mine`, `stats`, or `verify`.

## Assumptions

- A response is long when it contains at least 400 words. The CLI will expose this threshold and record it in the manifest.
- A turn's response is the last visible assistant message before the next user-authored message. This excludes tool preambles when an agent records a later final answer.
- `no_revision_requested` is a useful mining label. It does not prove that the response was good.
- A conservative fixed phrase list can reject follow-ups that ask for another kind of style revision. The miner excludes those follow-ups from the acceptance proxy.
- Only the current conversation graph is mined from Cursor. Unsupported or missing roots produce issues. The adapter never guesses from row order.

## Package

Add a standard-library Python package at `response-style/`. Its command will be `response-style`.

```text
response-style mine \
  --unix-user onur \
  --pi-sessions <path> \
  --codex-sessions <path> \
  --claude-projects <path> \
  --cursor-chats <path> \
  --cursor-acp-sessions <path> \
  --output ~/.local/share/response-style-private

response-style stats --dataset ~/.local/share/response-style-private
response-style verify --dataset ~/.local/share/response-style-private
```

Every source option is optional, but at least one must be supplied. The command will not scan a home directory to discover sources.

## Dataset files

The output directory contains private conversation examples in `examples.jsonl`. Bounded source locations and error codes go in `issues.jsonl`, which contains no conversation text. The `manifest.json` file records the schema version, settings, counts, source kinds, and file digests.

Each example uses this version 1 shape:

```json
{
  "schema_version": 1,
  "example_id": "sha256:<hex>",
  "kind": "revision_requested",
  "source_agent": "pi",
  "source_session_id": "session-id",
  "source_branch_id": "leaf-message-id",
  "source_relative_path": "project/session.jsonl",
  "initial_message_id": "assistant-message-id",
  "query_message_id": "user-message-id",
  "final_message_id": "assistant-message-id",
  "initial_assistant_response": "Original response",
  "user_query": "amk",
  "final_assistant_response": "Rewritten response",
  "matched_terms": ["amk"],
  "initial_word_count": 120,
  "final_word_count": 35
}
```

`kind` is `revision_requested`, `continued_without_revision`, or `conversation_ended`. The latter two are the `no_revision_requested` acceptance proxy. They store the long response in `initial_assistant_response`, and `final_assistant_response` is null. `user_query` is the next user message when one exists and null when the conversation ended. Length comparisons are derived from the two word counts instead of being stored as another field.

## Source handling

### Pi and Claude Code

Build the native message tree from message IDs and parent IDs. Walk every root-to-leaf path, reduce it to user-authored queries and visible assistant responses, mine adjacent turns, and deduplicate examples by their source message IDs. Reject malformed parent graphs and record malformed JSONL lines as issues.

Claude Code user records with a sidechain agent ID, system prompt source, task notification, SDK source, or known injected wrapper are not user-authored messages.

### Codex

Use `event_msg.user_message` as the user-authored query. Use canonical `response_item.message` records with `phase = final_answer` as assistant responses. Accept legacy assistant messages without a phase. Ignore commentary, developer messages, copied user projections, tool records, and event projections.

### Cursor

Open each `store.db` with SQLite read-only and query-only settings. Decode the latest conversation root's repeated message blob IDs with a small checked protobuf wire reader. Read only strict JSON message blobs reachable from that root. Keep `user` text and `assistant` text blocks; ignore reasoning and tool roles. Reject missing or unsupported roots. The adapter never uses SQLite row order as a fallback.

## Deterministic mining

1. Normalize each source path into ordered conversation turns. Join consecutive user-authored messages before the next assistant response, preserving their order and using the last message as the query boundary.
2. For adjacent turns, emit `revision_requested` when the later query contains `amk` or `plain` as a complete word and both responses exist.
3. For every response at or above the long-response threshold, emit `no_revision_requested` when the next query contains neither the trigger words nor a conservative style-revision phrase. A terminal response uses `conversation_ended`.
4. Derive IDs from the schema version, source agent, session, branch, and source message IDs.
5. Use the last source message represented by an example as its branch boundary, so later appends to the same conversation do not change existing rows. Sort rows by agent and relative source path, then by session and message IDs within each branch boundary.
6. Write all files to a private temporary directory, verify them, then replace the previous dataset atomically.

The extractor will preserve matched content even when it contains secrets. The output directory is private because redaction would change the examples.

The draft schema passed Schemator's local extraction smoke test. The configured semantic reviewer could not run because its Codex account had reached its usage limit, so the schema received a manual product pass. That pass removed the redundant `followup_kind` and derived `became_shorter` fields and replaced the two overlapping selectors with one three-value `kind` field.

## Validation

Synthetic tests will cover:

- Exact trigger matching and false substring matches.
- Long-response thresholds and the conservative style-revision phrase list.
- Pi and Claude branches plus tool-only messages. Cover sidechains and malformed lines in the same fixtures.
- Codex user events, commentary exclusion, final answers, and legacy messages.
- Cursor protobuf order, text-only extraction, missing roots, and read-only SQLite access.
- Stable IDs, duplicate branch prefixes, deterministic sorting, private permissions, atomic replacement, and manifest digests.
- Proof that summary commands print counts only.

Run:

```text
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest --cov=response_style --cov-fail-under=85
uv run pip-audit
uvx slophammer-py@0.4.0 check . --execute
npx -y @simpledoc/simpledoc check
```

Then run a private full extraction from the five local roots, verify the result, rerun it unchanged, and compare example-file digests. Do not print or commit any example text.

## Completion criteria

- All accessible source roots produce a valid private dataset or bounded issues.
- The output contains the two requested kinds with source provenance and length metrics.
- Repeating the same extraction against unchanged sources produces the same examples.
- No generated dataset file is tracked by Git or included in the pull request.
- Unit tests and repository checks pass.
- Pi Reviewer reports no P0 or P1 issue.
- CI passes before merge.
