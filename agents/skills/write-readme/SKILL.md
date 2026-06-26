---
name: write-readme
description: Use when creating, rewriting, or reviewing README files. Keeps READMEs focused on users and moves maintainer process details to maintainer docs.
---

# Write README

Use this skill when writing or reviewing README content.

The README is for users.

Use it for what someone needs to understand, install, and use the project.

Be direct and pragmatic. Do not write word diarrhea: avoid exhaustive feature
taxonomies, implementation internals, long option catalogs, CI details, or
process history unless a user needs them to install or use the project.

Keep maintainer process details out unless the project is itself a maintainer tool.

## Opening Intro

Start the first paragraph with what the project is, then what it does.

- First sentence: state the project's category or identity.
- Second sentence: state the practical job it performs for users.
- Avoid starting with only a verb-led feature claim; readers should not have to
  infer what kind of thing the project is.

Example:

```markdown
Schemator is a schema and data-model review CLI for agents.
It turns draft TypeScript, JSON Schema, YAML, JSON, or Markdown proposal snippets
into a reviewed field graph and applies safe simplifications until the model
stabilizes.
```

Examples of maintainer process details:

- release mechanics
- publishing setup
- CI internals
- credentials or trust setup
- historical notes about how the current release was made

Put those in maintainer docs when they need to exist.

## Demo Media

When adding asciinema, GIF, or video demos to a README:

- Prefer a hosted, playable demo link or embed over local playback instructions.
- Do not commit generated GIF/video assets to the repository just to make the
  README look animated.
- If the user has a local GIF or video, give them the local file path and tell
  them to upload it or drag/drop it into the README editor in the browser, then
  use the hosted URL in the README.
- It is okay to keep small source recordings only when the repository explicitly
  wants them as source artifacts; do not assume this for generated media.
