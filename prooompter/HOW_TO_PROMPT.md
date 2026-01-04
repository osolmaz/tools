---
date: 2025-11-16
author: Head of Prooompting
title: Prompt Assembly Guide
tags: [tooling, context]
---

# ATTENTION AGENT!

This is a guide. If this file is tagged in a user instruction, execute the steps immediately—no extra confirmation loops. The goal is to collect a focused bundle of source files using `prooompter`, keeping the payload under the configured character limit.

# Prompt Assembly Playbook

Follow this workflow whenever you are asked to "gather files for a prompt" or "build a context bundle" for downstream tooling.

## 1. Prepare the Candidate List

- Start with the file list provided by the user. Preserve the order—most relevant at the top, least relevant at the bottom.
- If you need to add files (e.g., dependencies or helper modules), insert them near related entries and state why in your final message.
- Keep a copy of the ordered list so you can remove items systematically if the output exceeds the character cap.

## 2. Run `prooompter`

Use the CLI directly—no wrapper scripts unless the user supplied one:

```bash
prooompter \
  path/to/file1 \
  path/to/file2 \
  path/to/file3
```

When working inside a uv environment, prefer `uv run prooompter …` so dependencies resolve consistently.

Best practices:

- Run the command from the repository root (or whichever directory makes the relative paths valid).
- Allow the default behavior: the tool writes to a temporary file and prints that path to stderr when successful.
- If you need stdout output for immediate inspection, pass `--output -`, but remember the character limit still applies.

## 3. Handle Character Limit Errors

`prooompter` raises a ClickException when the payload exceeds the limit (default: 400,000 characters, configurable via `--max-chars` or `prooompter.toml`). When that happens:

1. Remove the least relevant file from your ordered list.
2. Re-run the command with the remaining paths.
3. Repeat until the command succeeds within the limit.

Guidelines while trimming:

- Remove one file at a time so you can report exactly what changed.
- Always drop the lowest-priority file first. Honor any priority ranking supplied by the user.
- If you must remove a file that seems critical, pause and ask the user before proceeding.

## 4. Report the Result

After a successful run:

- Capture the temporary file path printed by the CLI and include it in your response.
- List the final set of files included, in order, so the user can see what remained.
- If you removed files due to size, mention each exclusion and note that the character limit triggered the change.
- If the user wants the contents inline, re-run with `--output - --max-chars 0` and stream carefully, but only after they confirm.

## 5. Optional Enhancements

- Save reusable defaults (ignore patterns, alternate max sizes, etc.) in `prooompter.toml` at the repository root.
- Use `--max-chars <N>` to tighten or relax the cap if the user specifies a different target.
- Combine with search tools (`rg --files` piped into `prooompter`) when the user asks for “all files matching X”. Apply the same deletion procedure if the output exceeds the limit.

Stay disciplined: run the command, watch for the limit, trim from the bottom, and surface the final bundle back to the user.

---

## 6. Document the Problem Context

- When the task includes a clear problem statement (e.g., a reproducible bug or user complaint), append a concise **Problem Description** section at the end of your final report to capture it.
- Use bullet points that summarize symptoms, suspected causes, and impact. Keep it short—aim for 3–5 bullets.
- If the problem is ambiguous or you needed to remove high-priority files to meet the character limit, call that out alongside the problem description.
- Skip this section only when the user explicitly asks for raw output without commentary.
