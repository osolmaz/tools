---
name: openclaw-onur-inventory
description: Use when maintaining ~/scratch/OPENCLAW_LOCAL_MODEL_OPEN_THREADS.md, auditing OpenClaw local model and open-weight model issue/PR inventories, deciding whether a thread belongs in that file, sorting the inventory, or explaining why an item was included or excluded.
---

# OpenClaw Onur Inventory

Use this skill for `~/scratch/OPENCLAW_LOCAL_MODEL_OPEN_THREADS.md`.

The inventory is curated. Do not regenerate it by dumping keyword hits.

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
4. Review every candidate one by one. Keep direct/material matches and drop incidental body/comment/label matches.
5. Put closed or removed notable threads under the existing collapsed `<details>` block so they do not bloat the open inventory.
6. Keep open issues and open PRs in separate tables.
7. Run `python3 scripts/sort_openclaw_local_model_threads.py` before committing so issue, PR, and closed/removed tables stay newest-first by GitHub number.
8. Recount rows and compare the retained issue/PR number sets before committing.

## Output Expectations

- Say whether counts are issues, PRs, or combined threads.
- When challenged on one item, check the live issue/PR body before defending it.
- If an item was included only because a provider/model name appeared incidentally, remove it.
- Keep the final GitHub link handy: `https://github.com/dutifuldev/scratch/blob/main/OPENCLAW_LOCAL_MODEL_OPEN_THREADS.md`.
