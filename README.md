# personal tools of @osolmaz

This repository contains various tools that do not yet deserve their own repos.

Although it contains many tools, [`agents/`](agents/) has become the most important directory. It contains my [`AGENTS.md`](agents/AGENTS.md) instructions and specific skills for my workflows.

My Pi-specific extensions live in the separate [`osolmaz/onurpi`](https://github.com/osolmaz/onurpi) repository. I decided to keep them out of this monorepo.

![istockphoto-96356725-612x612](https://github.com/user-attachments/assets/781b5804-3ddf-4488-aae2-d0e4ac1e7433)

See [Having a "tools" repo as a developer](https://solmaz.io/tools-repo).

## Tools

- [`chardiff/`](chardiff/) is a character-level diff tool in a single HTML page.
- [`claude-code-data/`](claude-code-data/) is a library for parsing and analyzing Claude Code conversation files.
- [`codex-tools/`](codex-tools/) inspects and repairs local Codex session metadata.
- [`padify/`](padify/) adds padding to images, which is handy for terminal screenshots.
- [`pngscrub/`](pngscrub/) inspects and removes private PNG metadata without changing image data.
- [`prooompter/`](prooompter/) constructs prompts from files that fit the context window.
- [`agents/skills/`](agents/skills/) contains repo-local skills for autonomous implementation and PR follow-through.
- [`agents/prompts/`](agents/prompts/) contains reusable prompts for plan-driven implementation, PR triage, and autonomous landing.
- [`rmdbg/`](rmdbg/) removes debugger statements from Python source code.
- [`spawn/`](spawn/) is a small CLI coding agent orchestrator.
- [`tilekit/`](tilekit/) generates balanced, non-overlapping image tile patterns.
- [`transcribe/`](transcribe/) contains CLIs for converting voice messages into text.
- [`agents/workflows/`](agents/workflows/) contains orchestration docs for prompt-driven PR automation.

## Process docs

- [PR automation workflow](agents/workflows/pr-automation.md)
- [Autoimplement skill](agents/skills/autoimplement/SKILL.md)
- [Implementation plan prompt](agents/prompts/implement-plan.md)
- [PR / issue triage prompt](agents/prompts/pr-issue-triage.md)
- [Land-ready PR prompt](agents/prompts/land-ready-pr.md)
