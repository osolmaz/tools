---
name: wiki
description: Use when creating, restructuring, naming, or hydrating durable wiki-style pages in a workspace.
---

# Wiki

Use this skill when the user asks for a wiki, wiki pages, durable reference
pages, topic indexes, or stable knowledge pages in a workspace.

Wiki pages are stable navigation and synthesis pages. They should feel like
durable reference, not generated article titles or one-off dated notes.

## Rules

- Put wiki work in the workspace, not only in an external repo, dataset, or
  published artifact.
- Use the relevant workspace area for the topic, then a `wiki/` subfolder when
  the topic needs stable navigation.
- Preserve existing external notes, dataset files, published docs, or pages
  unless the user explicitly asks to remove, relocate, or unpublish them.
- Use SimpleDoc capitalized-file style for wiki pages: all-caps words,
  underscores between words, `.md` extension.
- Prefer short, lindy page names over long generated titles.
- Keep names topic-like, not sentence-like.
- Keep `README.md` as the index for each wiki folder.
- If a general workspace wiki index exists, point it at the canonical topic
  wiki pages instead of creating competing canonical pages.
- Keep dated SimpleDoc docs as source/history pages when they already exist;
  make the wiki pages the stable navigation layer.

## Naming

Good:

- `LOCAL_INFERENCE.md`
- `BENCHMARKS.md`
- `NVIDIA_GB10.md`
- `APPLE_SILICON.md`
- `DEMO_GRID.md`

Avoid:

- `Local_Inference_Performance_Goal.md`
- `Model_Benchmarking_Throughput.md`
- `2026-06-19-local-inference-performance-goal.md` as the canonical wiki page

## Hydration

- Hydrate wiki pages only from user-corrected, established, or sourced context.
- Do not invent a broad taxonomy unless the user asks for one.
- Do not overfit the wiki to a single dated conversation; extract the durable
  page shape and stable facts.
- When the user corrects placement, naming, or scope, update the wiki structure
  to match that correction.

## Workflow

1. Check repo status before editing.
2. Read existing related wiki pages and indexes.
3. Choose the correct workspace area and `wiki/` folder.
4. Pick short all-caps underscore filenames.
5. Create, rename, or hydrate pages.
6. Update the local wiki `README.md` and any higher-level workspace index.
7. Preserve external or published artifacts unless explicitly asked to change
   them.
8. Run the repo's doc checks when available. If failures are pre-existing,
   report that clearly.
9. Sync or commit through the repo's normal workflow when the workspace expects
   durable changes to be saved.
