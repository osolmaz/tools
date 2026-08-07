# Response Style

Response Style is a local dataset-mining CLI for coding-agent conversations. It finds response rewrites requested with `amk` or `plain` and long responses that received no style-revision request.

The generated dataset can contain private conversation text and secrets. The CLI writes it to a private local directory, refuses output inside a Git worktree, and never sends it over the network. Keep the dataset private until you review and sanitize it.

## Install

Response Style requires Python 3.12 or newer.

```sh
uv sync --locked
```

## Mine conversations

Pass every source root explicitly:

```sh
uv run response-style mine \
  --unix-user "$USER" \
  --pi-sessions ~/.pi/agent/sessions \
  --codex-sessions ~/.codex/sessions \
  --claude-projects ~/.claude/projects \
  --cursor-chats ~/.cursor/chats \
  --cursor-acp-sessions ~/.cursor/acp-sessions
```

The default output is `~/.local/share/response-style-private`. It contains:

- `examples.jsonl`, with the private conversation examples.
- `issues.jsonl`, with source locations and bounded error descriptions.
- `manifest.json`, with settings and counts together with file digests.

A response is considered long at 400 words by default. Change that threshold with `--long-word-count`.

## Inspect without printing conversations

```sh
uv run response-style stats
uv run response-style verify
```

Both commands print counts and hashes only. They never print conversation text.

## Labels

`revision_requested` records the response before an `amk` or `plain` request, the request, and the assistant's next response.

`continued_without_revision` records a long response followed by another user request that contains no known style-revision signal.

`conversation_ended` records a long terminal response. The two no-revision labels are useful acceptance proxies, but they do not prove that the response was good.
