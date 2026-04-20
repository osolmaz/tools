---
name: pr-description
description: Use when opening a pull request, or when asked to write or improve a pull request description. Produces a plain summary up top, then structured technical sections with paired plain-language explanations.
---

# PR Description

Use this skill when writing a PR description.

When this skill is invoked, write a PR description that helps both reviewers and future readers.

The top summary must answer this question:

`bro, what the hell is this about?`

That means the summary should:

- lead with the real user-facing or developer-facing problem
- say what changed in simple words
- say why this fix matters
- use short full sentences
- avoid jargon unless it is required
- stand on its own without the rest of the PR

Write the top summary in the same style as the `plain-language` skill:

- short full sentences
- main point first
- concrete words
- no meta lead-ins
- no unnecessary bullets
- usually 2 to 4 sentences
- put each sentence on its own line

After the summary, use these sections by default unless the user asks for a different shape:

## Summary

- Plain first.
- This is the "what is this about?" section.
- Do not hide the main point behind implementation details.

## What Changed

- Technical section.
- Explain the real code or behavior changes.
- Group related changes together instead of listing every file.

## Plain Language

- Required after `What Changed`.
- Restate the same thing in simpler words.
- Someone who does not know the codebase should still understand the change.

## Testing

- Say exactly what was tested.
- Include commands when they matter.
- Say what was not tested.

## Plain Language

- Required after `Testing` if the testing section is technical.
- Explain what the tests prove in simpler words.

## Risks

- Call out real risks, limitations, or edge cases.
- If risk is low, say why.

## Plain Language

- Required after `Risks` if the risk discussion is technical.
- Explain the practical takeaway in simpler words.

## Follow-ups

- Optional.
- Use only for real remaining work.
- Do not invent future work just to fill space.

## Rules

- Every technical jargon section should have a matching plain-language section.
- Do not make the reader decode acronyms or repo-specific shorthand without help.
- Do not write changelog fluff.
- Do not turn the summary into a bullet dump.
- Do not pretend untested behavior is verified.
- Do not say "this PR" in every sentence when a direct sentence is clearer.
- Prefer direct statements over sales language.

## Good Pattern

```md
## Summary

Users could hit a dead end when the picker failed.
This change makes the picker fall back safely instead of crashing.
It also adds tests for the bad cases we actually saw.

## What Changed

- Added a shared helper for safe channel metadata access.
- Switched the picker and slash-command paths to use that helper.
- Added regression tests for partial channel objects.

## Plain Language

The app was reading Discord channel fields in a way that could crash.
Now both command paths use the same safe code, and the broken cases are covered by tests.

## Testing

- `pnpm exec vitest run extensions/discord/src/monitor/native-command.commands-allowfrom.test.ts`
- `pnpm exec vitest run extensions/discord/src/monitor/native-command.model-picker.test.ts`
- `pnpm build`

## Plain Language

I tested the two paths that were breaking, and I also made sure the project still builds.

## Risks

- This only covers the command and picker paths.
- Other Discord surfaces may still have direct partial-channel reads.

## Plain Language

The known bug should be fixed here.
There may still be similar bugs elsewhere in the Discord code.
```

## Bad Pattern

```md
## Summary

This PR introduces a generalized metadata abstraction layer for partial-channel-safe command execution across heterogeneous Discord interaction surfaces.
```

Better:

```md
## Summary

Some Discord commands could crash before replying.
This change makes them read channel data safely and adds tests for the broken cases.
```
