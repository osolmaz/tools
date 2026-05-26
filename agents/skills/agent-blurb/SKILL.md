---
name: agent-blurb
description: Write README prompts that tell coding agents how to adopt a tool.
---

# Agent Blurb

Use this skill to write a short README blurb that a human can copy into a
coding agent. The blurb should tell the agent exactly what to do with a tool,
project standard, or workflow.

## Principles

- Treat the blurb as setup instructions for an agent, not product marketing.
- Address two audiences:
  - Human lead-in text says when to copy the block and what it will do.
  - The fenced block addresses the coding agent directly.
- Keep the copy concise enough to paste comfortably into a chat or agent
  prompt.
- Wrap prose and prompt text to 80 characters or less when practical.
- Put the prompt in a fenced `text` code block so GitHub renders a clean
  copyable block.
- Start the prompt with the desired outcome and the project or tool name.
- Point to the source of truth before asking the agent to change files. Use an
  `AGENT_ENTRYPOINT.md`, install doc, README section, or stable raw URL when
  the repo has one.
- Include exact commands when they are stable. Otherwise, tell the agent which
  doc to read and follow.
- Ask the user only for facts the agent cannot infer, such as target repo, OS,
  account choice, secret location, or approval for destructive actions.
- Tell the agent how to verify the result and what to report back.
- Make the instructions idempotent: inspect existing setup first, then update
  it instead of duplicating config.
- Include safety boundaries for secrets, external writes, and destructive
  actions when the task can touch them.
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
2. Decide whether the project needs a short source-of-truth pointer or a fuller
   action prompt.
3. Add a short human lead-in followed by one fenced `text` block.
4. Keep the block short, direct, and wrapped to 80 characters.
5. Check that the prompt asks the human only for missing information and gives
   the agent a verification step.

## Template

````md
### Ask your coding agent (recommended)

Copy this block and paste it into your coding agent when you want it to
<outcome>.

```text
Use <tool> to <outcome> for this project.

Attention agent: start with this source of truth before changing files:
<url-or-path>

Please do the following:
1. Inspect <context> and detect what is already installed or configured.
2. Ask me only for missing choices: <choices>.
3. Install or configure <tool> using the documented commands.
4. Verify the result with <checks>.
5. Report what changed and anything I still need to do.

Safety:
- Ask before destructive changes or external writes.
- Never ask me to paste secrets into chat; use placeholders or local files.
- Do not duplicate existing config; update it in place when possible.
```
````

Prefer a shorter prompt when the project already has a strong agent entrypoint:

````md
## Quick setup: tell your agent about <Tool>

Copy this block and paste it into your coding agent when you want it to use
<Tool> in this repository.

```text
Use <Tool> to <outcome> for this project.

Attention agent: start with this file before changing code:
<raw-url-or-repo-path>

Follow it exactly. Detect the target repo's context, apply the matching
instructions, and say clearly if the requested setup is not supported.
```
````
