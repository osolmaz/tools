# Upstream provenance

The reference library vendors the documentation from the Modular
[LLM Inference Handbook](https://github.com/modular/llm-inference-handbook).
The rendered handbook is available at
[handbook.modular.com](https://handbook.modular.com/).

The vendored snapshot is
`317b9816ec3080031333ed9ee44dfce919763bf7`, dated 2026-07-24. Its documentation
uses the CC BY 4.0 license reproduced in
[references/LICENSE](references/LICENSE). The previous skill snapshot came from
`bentoml/llm-inference-handbook` at
`ea07b2ccd9b35db810763fc76980b26be1d2b871`.

The Modular repository continues the same Git history as the earlier BentoML
repository. The previous snapshot is an ancestor of the current Modular
snapshot. This skill therefore keeps one current reference library instead of
storing the same handbook twice under different publisher names.

## Changes to the documentation source

The prose is copied from the pinned upstream snapshot. The vendor script makes
these mechanical changes so the files work as standalone Markdown:

- It converts section index files from `.mdx` to `.md`.
- It removes Docusaurus imports, card lists, and other site-only wrappers.
- It replaces interactive components with links to their rendered pages.
- It rewrites diagrams and images to immutable URLs at the pinned commit.
- It rewrites handbook-internal routes as relative links between vendored
  Markdown files.

Run the import from the repository root with:

```bash
python3 agents/skills/llm-inference-fundamentals/scripts/vendor_handbook.py \
  /path/to/modular-llm-inference-handbook
```

The script refuses a checkout whose commit differs from its pinned revision.
Updating the handbook requires changing that pin deliberately, reviewing the
upstream diff and license, regenerating the references, and validating every
local link.
