---
name: openclaw-onur-inventory
description: Use when maintaining ~/repos/onurclaw/OPENCLAW_ONUR_INVENTORY.md, including periodic roughly every-2-hour refreshes, auditing OpenClaw local model and open-weight model issue/PR inventories, deciding whether a thread belongs in that file, sorting the inventory, updating the reviewed-through issue/PR watermark, or explaining why an item was included or excluded.
---

# OpenClaw Onur Inventory

Use this skill for `~/repos/onurclaw/OPENCLAW_ONUR_INVENTORY.md`.

The inventory is curated. Do not regenerate it by dumping keyword hits.

The source for this skill is `~/repos/tools/agents/skills/openclaw-onur-inventory`. Do not edit or create duplicate copies under `~/bob/skills/openclaw-onur-inventory`; sync from the tools repo source into installed/runtime skill locations instead.

## Periodic Cadence

Run this inventory maintenance periodically, normally about every 2 hours when the user asks for ongoing upkeep.

Each run must refresh live state, scrutinize candidates, update/curate the onurclaw inventory file if anything changed, sort it, and commit/push the onurclaw repo changes.

For unattended automation, use the public hardened job contract in `~/repos/onurclaw/docs/inventory-job.md` and the checked-in wrapper `~/repos/onurclaw/scripts/run_inventory_job.sh`. The cron prompt must only ask the agent to run that wrapper. Do not document or expose host-specific paths, credentials, message destinations, or the private security topology in public files. The automated runner must use an isolated sandbox, read-only exported Gitcrawl/notifier data, no network egress, and an exec allowlist for the wrapper only.

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

1. Work in `~/repos/onurclaw`.
2. Verify Gitcrawl freshness and fetch live GitHub open issue/PR state.
3. Build a broad candidate pool from local/open-weight/provider terms.
4. You must review every candidate one by one. Keep direct/material matches and drop incidental body/comment/label matches.
5. Put closed or removed notable threads under the existing collapsed `<details>` block so they do not bloat the open inventory.
6. Update the `Review watermark` near the top of the file with the highest live GitHub issue number and highest live GitHub PR number that were covered by the review.
7. Keep open issues and open PRs in separate tables.
8. Run the sorter before committing so open issue and PR tables sort by `Activity` score descending, then GitHub number descending, while closed/removed tables stay newest-first by GitHub number and open-thread activity scores are refreshed.
9. Recount rows and compare the retained issue/PR number sets before committing.

## File Shape

Keep the inventory file terse. The top of the file must contain only:

- title
- `Updated: YYYY-MM-DD`
- `Review watermark`
- open issue table
- open PR table
- collapsed closed/removed details
- short regeneration notes

Do not add or maintain these noisy generated sections:

- `Sources checked`
- `Audit result`
- `Inclusion criteria used`
- `HIGHEST-RISK OPEN AREAS`
- cumulative per-run source logs or review-range logs
- broad candidate counts unless the user explicitly asks for an audit report

Put audit details, source freshness, candidate counts, and rationale summaries in the chat response, commit message, or PR body instead of the inventory file.

## Review Watermark

The inventory must include a `Review watermark` section near the top of `~/repos/onurclaw/OPENCLAW_ONUR_INVENTORY.md`.

Record:

- `Last reviewed through issue: #<number>`
- `Last reviewed through PR: #<number>`

Only advance these numbers after the run has considered all issues or PRs up to those numbers. If a run only reviews a subset, leave the corresponding watermark unchanged and say what range remains unchecked.

## Sorter

The sorter is bundled with this skill at `scripts/sort_openclaw_onur_inventory.py`.

From the tools repo source, run:

```bash
python3 ~/repos/tools/agents/skills/openclaw-onur-inventory/scripts/sort_openclaw_onur_inventory.py ~/repos/onurclaw/OPENCLAW_ONUR_INVENTORY.md
```

By default the sorter also refreshes the `Activity` column for open issues and PRs using authenticated `gh api` calls. It sorts open issue and PR rows by `Activity` score descending, then GitHub number descending. It keeps sorting/counting even if an activity lookup fails, and prints warnings for skipped threads. Use `--no-activity` or `OPENCLAW_ONUR_INVENTORY_SKIP_ACTIVITY=1` only for tests or emergency offline sorting.

If the onurclaw repo has its own checked-in copy, this is also acceptable:

```bash
cd ~/repos/onurclaw && python3 scripts/sort_openclaw_onur_inventory.py
```

## Activity Score

The `Activity` column is a single weighted, human-only count of current visible GitHub activity. It is the only priority-like ranking column in the open issue and PR tables; do not keep a separate `Priority` column.

Open issue and PR tables must use this column order:

- `Issue` or `PR`
- `Activity`
- `Area`
- `Title`

If a row has an assignee, put `Assignee: <name>` below the title in the `Title` cell.

Weights:

- First issue or PR conversation comment by a human account: `4`
- Additional issue or PR conversation comments by the same human account: `1`
- First PR review comment by a human account: `4`
- Additional PR review comments by the same human account: `1`
- First PR review body with non-empty text by a human account: `5`
- Additional PR review bodies with non-empty text by the same human account: `1`
- Reaction on the issue/PR body, conversation comments, or PR review comments: `1`

Classification and filtering:

- Count non-human activity separately by excluding it from the `Activity` score. An actor is non-human when GitHub reports the actor type as `Bot` or the login ends with `[bot]`.
- Exclude `osolmaz` and `dutifulbob` from the `Activity` score by default.
- Use `--ignored-account <login>` to add more excluded human accounts. This can be repeated. `OPENCLAW_ONUR_INVENTORY_IGNORED_ACCOUNTS` can also provide a comma-separated list.
- When GraphQL exposes minimized comment metadata, exclude comments where `isMinimized=true` and `minimizedReason=SPAM`.
- The current `Activity` cell format is only the total score, for example `45` on an issue or `82` on a PR.
- Open issues and open PRs must be sorted first by `Activity` score descending, then by GitHub issue/PR number descending.
- Closed or removed rows stay sorted by GitHub issue/PR number descending because they do not carry live activity ranking.

## Output Expectations

- Say whether counts are issues, PRs, or combined threads.
- When challenged on one item, you must check the live issue/PR body before defending it.
- If an item was included only because a provider/model name appeared incidentally, you must remove it.
- Keep the final GitHub link handy: `https://github.com/osolmaz/onurclaw/blob/main/OPENCLAW_ONUR_INVENTORY.md`.
