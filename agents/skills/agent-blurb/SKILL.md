---
name: agent-blurb
description: Write README prompts that tell coding agents how to adopt a tool.
---

# Agent Blurb

Use this skill to write a short README blurb that a human can copy into a
coding agent. Default to the shortest prompt that still tells the agent what
to use, where to start, what to ask, and how to verify.

## Principles

- Treat the blurb as setup instructions for an agent, not product marketing.
- Address two audiences:
  - Human lead-in text says when to copy the block and what it will do.
  - The fenced block addresses the coding agent directly.
- Prefer 4-8 lines inside the fenced block. Go longer only when setup has
  multiple real steps.
- Keep the surrounding human lead-in to one short sentence when possible.
- Wrap prose and prompt text to 80 characters or less when practical.
- Put the prompt in a fenced `text` code block so GitHub renders a clean
  copyable block.
- Start the prompt with the desired outcome and the project or tool name.
- Point to the source of truth before asking the agent to change files. Use an
  `AGENT_ENTRYPOINT.md`, install doc, README section, or stable raw URL when
  the repo has one.
- Include exact commands only when they are essential. Otherwise, point to the
  source of truth.
- Ask the user only for facts the agent cannot infer, such as target repo, OS,
  account choice, secret location, or approval for destructive actions.
- Tell the agent how to verify the result and what to report back.
- Make the instructions idempotent: inspect existing setup first, then update
  it instead of duplicating config.
- Include safety boundaries only when the task can touch secrets, external
  writes, or destructive actions.
- Avoid branding the section as "Agent Blurb". Name it as an action the reader
  can take.

## README Placement

Group the blurb with the existing install, quickstart, or setup instructions.
Do not create several separate agent sections.

Good section names:

- `## Quick setup: tell your agent about <Tool>`
- `## Quick setup - tell your agent about <Tool>`
- `### Ask your coding agent (recommended)`
- `### Agent-assisted setup`

Use a top-level quick setup section when the README has no install section yet.
Use a subsection when the README already has an install, quickstart, or setup
section.

## Workflow

1. Inspect the README and install docs to find the natural setup section.
2. Start with a short source-of-truth pointer. Expand only if the agent would
   otherwise miss important setup steps.
3. Add a short human lead-in followed by one fenced `text` block.
4. Keep the block short, direct, and wrapped to 80 characters.
5. Cut any line that repeats the README or does not change agent behavior.

## Template

````md
### Ask your coding agent (recommended)

Copy this block and paste it into your coding agent when you want it to
<outcome>.

```text
Use <Tool> to <outcome> for this project.

Attention agent: start here before changing files:
<url-or-path>

Inspect the existing setup, update it in place, verify with <checks>, and
ask me only for missing choices: <choices>.
```
````

Add safety lines only when they are relevant:

````md
```text
Ask before destructive changes or external writes. Never ask me to paste
secrets into chat; use placeholders or local files.
```
````

Prefer an even shorter prompt when the project already has a strong agent
entrypoint:

````md
## Quick setup: tell your agent about <Tool>

Copy this block into your coding agent to use <Tool> in this repository.

```text
Use <Tool> to <outcome> for this project.

Attention agent: start here before changing code:
<raw-url-or-repo-path>

Follow it exactly. Report if the requested setup is unsupported.
```
````
