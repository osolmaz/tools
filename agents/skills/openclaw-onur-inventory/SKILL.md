---
name: openclaw-onur-inventory
description: Use when maintaining ~/scratch/OPENCLAW_ONUR_INVENTORY.md, including periodic roughly every-2-hour refreshes, auditing OpenClaw local model and open-weight model issue/PR inventories, deciding whether a thread belongs in that file, sorting the inventory, updating the reviewed-through issue/PR watermark, or explaining why an item was included or excluded.
---

# OpenClaw Onur Inventory

Use this skill for `~/scratch/OPENCLAW_ONUR_INVENTORY.md`.

The inventory is curated. Do not regenerate it by dumping keyword hits.

## Periodic Cadence

Run this inventory maintenance periodically, normally about every 2 hours when the user asks for ongoing upkeep.

Each run must refresh live state, scrutinize candidates, update/curate the scratch file if anything changed, sort it, and commit/push the scratch repo changes.

## Include Or Exclude

Keep a GitHub issue or PR only when the actual reported behavior or change is materially about at least one of:

- local model runtime or serving: Ollama, LM Studio, vLLM, llama.cpp, GGUF, MLX, local one-shot infer, local event-loop stalls, or local GPU/CPU serving paths
- self-hosted/OpenAI-compatible/proxy routing: OpenAI-compatible HTTP, openai-completions/responses, LiteLLM, Open-WebUI, custom baseUrl/provider, self-hosted embedding/ASR/TTS endpoints
- local memory/model infrastructure: QMD, local embeddings, memory embedding providers, rerankers, vector/FTS behavior, mixed vector spaces
- model routing correctness: fallback chains, model picker/switch, provider catalogs, auth-profile selection, actual backend model reporting, provider/model registry correctness
- open-weight/provider-family behavior when that model family is part of the bug or fix: Kimi, Qwen, DeepSeek, Moonshot, GLM/Z.ai, Gemma, Mistral, MiMo/Xiaomi, Nemotron, and similar provider paths

Drop generic channel, UI, gateway, cron, install, docs, memory, or bootstrap threads when a local/open-weight term is only incidental evidence.

Example exclusion: a remote native Moonshot/Kimi Discord dispatch delay is not local-model related unless the issue is specifically about local/self-hosted/OpenAI-compatible routing, local runtime behavior, or local embeddings.

## Refresh Workflow

1. Work in `~/scratch`.
2. Verify Gitcrawl freshness and fetch live GitHub open issue/PR state.
3. Build a broad candidate pool from local/open-weight/provider terms.
4. You must review every candidate one by one. Keep direct/material matches and drop incidental body/comment/label matches.
5. Put closed or removed notable threads under the existing collapsed `<details>` block so they do not bloat the open inventory.
6. Update the `Review watermark` near the top of the file with the highest live GitHub issue number and highest live GitHub PR number that were covered by the review.
7. Keep open issues and open PRs in separate tables.
8. Run the sorter before committing so issue, PR, and closed/removed tables stay newest-first by GitHub number.
9. Recount rows and compare the retained issue/PR number sets before committing.

## Review Watermark

The inventory must include a `Review watermark` section near the top of `~/scratch/OPENCLAW_ONUR_INVENTORY.md`.

Record:

- `Last reviewed through issue: #<number>`
- `Last reviewed through PR: #<number>`

Only advance these numbers after the run has considered all issues or PRs up to those numbers. If a run only reviews a subset, leave the corresponding watermark unchanged and say what range remains unchecked.

## Sorter

The sorter is bundled with this skill at `scripts/sort_openclaw_local_model_threads.py`.

From the tools repo source, run:

```bash
python3 ~/repos/tools/agents/skills/openclaw-onur-inventory/scripts/sort_openclaw_local_model_threads.py ~/scratch/OPENCLAW_ONUR_INVENTORY.md
```

If the scratch repo has its own checked-in copy, this is also acceptable:

```bash
cd ~/scratch && python3 scripts/sort_openclaw_local_model_threads.py
```

## Output Expectations

- Say whether counts are issues, PRs, or combined threads.
- When challenged on one item, you must check the live issue/PR body before defending it.
- If an item was included only because a provider/model name appeared incidentally, you must remove it.
- Keep the final GitHub link handy: `https://github.com/dutifuldev/scratch/blob/main/OPENCLAW_ONUR_INVENTORY.md`.
