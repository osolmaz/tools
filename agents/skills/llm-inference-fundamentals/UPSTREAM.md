# Upstream sources and licenses

This skill preserves two attributed editions from the same handbook lineage.
BentoML joined Modular through a strategic product acquisition announced on
2026-02-10:

- https://www.modular.com/blog/bentoml-joins-modular
- https://www.bentoml.com/blog/bentoml-is-joining-modular

The corporate relationship and shared Git history are explicit. The editions
remain separate here because their snapshots use different branding and
content.

## BentoML edition

The BentoML source is
https://github.com/bentoml/llm-inference-handbook. This skill pins commit
`ea07b2ccd9b35db810763fc76980b26be1d2b871` from 2026-07-01 under
[references/bentoml](references/bentoml/introduction.md). Its documentation uses
CC BY 4.0, reproduced in
[references/bentoml/LICENSE](references/bentoml/LICENSE).

The pinned commit preserves the earlier BentoML edition. The BentoML and Modular
repository URLs currently expose the same later `main` commit, but this older
snapshot remains a distinct source state.

## Modular edition

The Modular source is
https://github.com/modular/llm-inference-handbook, rendered at
https://handbook.modular.com. This skill pins commit
`317b9816ec3080031333ed9ee44dfce919763bf7` from 2026-07-24 under
[references/modular](references/modular/index.md). Its documentation also uses
CC BY 4.0, reproduced in
[references/modular/LICENSE](references/modular/LICENSE).

At both pinned commits, files under `docs/` use CC BY 4.0 while repository code
outside `docs/` uses Apache-2.0. The previous skill snapshot mistakenly copied
the root Apache license beside the vendored documentation. This import corrects
that error by preserving each snapshot's `docs/LICENSE` file.

## Import transformations

The source prose is kept intact. The vendor script makes only the mechanical
changes needed for local Markdown readers:

- Convert MDX section indexes to `.md`.
- Remove imports, newsletter forms, card-list placeholders and marketing
  buttons.
- Unwrap layout-only components.
- Replace interactive widgets with links to their rendered pages.
- Pin images to the relevant source repository and commit.
- Rewrite internal routes to local Markdown files.

The merged reasoning in `SKILL.md` is original synthesis. It is not represented
as verbatim text from either handbook. Product-specific examples and quotations
must retain their source attribution.

## Reproduce the import

Use clean checkouts at the pinned commits:

```bash
python3 scripts/vendor_handbooks.py \
  --bentoml-source /path/to/bentoml-handbook-checkout \
  --modular-source /path/to/modular-handbook-checkout
```

The script rejects a checkout at the wrong commit or with modified files under
`docs/`. Update either source specification deliberately when importing a newer
snapshot, then review that source's license and the synthesized guidance again.
