---
name: llm-inference-fundamentals
description: Domain knowledge for LLM inference and serving performance. Use when reasoning about inference benchmarks, serving configs, or performance trade-offs, or when explaining concepts such as TTFT, ITL, TPOT, throughput, goodput, prefill vs decode, KV cache, PagedAttention, continuous batching, prefix caching, speculative decoding, parallelism, quantization, GPU memory sizing, autoscaling, and inference infrastructure. This is reference knowledge, not a tool; it bundles the BentoML LLM Inference Handbook.
---

# LLM Inference Fundamentals

Use this skill as grounding when reasoning about LLM inference performance,
serving configuration, or benchmark interpretation. It vendors the BentoML
*LLM Inference Handbook* verbatim under [references/](references/).

## Source

- Upstream repository: https://github.com/bentoml/llm-inference-handbook
- Rendered site: https://bentoml.com/llm/
- Vendored commit: `ea07b2ccd9b35db810763fc76980b26be1d2b871` (2026-07-01)
- License: Apache-2.0, see [references/LICENSE](references/LICENSE)

The page text is verbatim from upstream. The only adjustments are mechanical:
site-only MDX widgets (newsletter boxes, interactive calculators and
visualizers, marketing call-to-action blocks) were removed, image links were
pinned to the upstream commit on raw.githubusercontent.com, and `.mdx` section
index pages were converted to plain `.md`. When quoting from these files,
attribute the handbook, not this repo.

## How to use

1. Do not read the whole handbook. Pick the one or two reference files that
   match the question from the index below.
2. Prefer the handbook's definitions when naming metrics (TTFT, TPOT, ITL,
   goodput) so terminology stays consistent across benchmarks and reports.
3. Distinguish server capacity from active workload shape: a large
   `max_model_len` or context window setting is not the same thing as a long
   active context. Decode cost depends on the tokens actually in the KV cache.
4. The interactive calculators from the website are not included, but the
   formulas they implement remain in the text.

## Index

Start here for orientation: [references/introduction.md](references/introduction.md)

### Basics — what inference is and how to measure it

- [what-is-llm-inference.md](references/llm-inference-basics/what-is-llm-inference.md) — inference vs the rest of the LLM lifecycle
- [how-does-llm-inference-work.md](references/llm-inference-basics/how-does-llm-inference-work.md) — prefill vs decode, autoregressive generation, context windows
- [llm-inference-metrics.md](references/llm-inference-basics/llm-inference-metrics.md) — TTFT, E2EL, TPOT, ITL, RPS, TPS, latency vs throughput vs goodput, SLOs
- [training-inference-differences.md](references/llm-inference-basics/training-inference-differences.md) — why inference workloads behave unlike training
- [cpu-vs-gpu-vs-tpu.md](references/llm-inference-basics/cpu-vs-gpu-vs-tpu.md) — hardware classes for inference

### Getting started — choosing models, frameworks, hardware

- [choosing-the-right-model.md](references/getting-started/choosing-the-right-model.md) — model selection and naming conventions
- [choosing-the-right-inference-framework.md](references/getting-started/choosing-the-right-inference-framework.md) — vLLM, SGLang, TensorRT-LLM, and friends
- [choosing-the-right-gpu.md](references/getting-started/choosing-the-right-gpu.md) — GPU selection criteria
- [calculating-gpu-memory-for-llms.md](references/getting-started/calculating-gpu-memory-for-llms.md) — weights + KV cache memory sizing
- [serverless-vs-self-hosted-llm-inference.md](references/getting-started/serverless-vs-self-hosted-llm-inference.md) — deployment model trade-offs
- [on-prem-llms.md](references/getting-started/on-prem-llms.md) — on-prem deployment
- [bring-your-own-cloud.md](references/getting-started/bring-your-own-cloud.md) — BYOC pattern

### Model preparation

- [llm-quantization.md](references/model-preparation/llm-quantization.md) — quantization formats and quality/perf trade-offs
- [llm-fine-tuning.md](references/model-preparation/llm-fine-tuning.md) — fine-tuning approaches
- [llm-distillation.md](references/model-preparation/llm-distillation.md) — distillation

### Model interaction — APIs and request shaping

- [openai-compatible-api.md](references/model-interaction/openai-compatible-api.md) — the de facto serving API
- [anthropic-compatible-api.md](references/model-interaction/anthropic-compatible-api.md) — Anthropic-compatible endpoints
- [inference-parameters.md](references/model-interaction/inference-parameters.md) — temperature, top-p/top-k, max tokens, sampling
- [prompt-engineering.md](references/model-interaction/prompt-engineering.md) — prompting techniques
- [function-calling.md](references/model-interaction/function-calling.md) — tool use
- [structured-outputs.md](references/model-interaction/structured-outputs.md) — constrained decoding
- [model-context-protocol.md](references/model-interaction/model-context-protocol.md) — MCP

### Inference optimization — the core performance chapter

- [llm-performance-benchmarks.md](references/inference-optimization/llm-performance-benchmarks.md) — how to benchmark and read benchmark numbers
- [static-dynamic-continuous-batching.md](references/inference-optimization/static-dynamic-continuous-batching.md) — batching strategies, chunked prefill
- [pagedattention.md](references/inference-optimization/pagedattention.md) — KV cache paging
- [prefix-caching.md](references/inference-optimization/prefix-caching.md) — KV reuse across requests
- [kv-cache-offloading.md](references/inference-optimization/kv-cache-offloading.md) — KV cache tiering to CPU/disk
- [speculative-decoding.md](references/inference-optimization/speculative-decoding.md) — draft models and acceptance rates
- [prefill-decode-disaggregation.md](references/inference-optimization/prefill-decode-disaggregation.md) — splitting prefill and decode fleets
- [data-tensor-pipeline-expert-hybrid-parallelism.md](references/inference-optimization/data-tensor-pipeline-expert-hybrid-parallelism.md) — DP/TP/PP/EP and hybrids
- [inference-routing.md](references/inference-optimization/inference-routing.md) — cache-aware and load-aware routing
- [offline-batch-inference.md](references/inference-optimization/offline-batch-inference.md) — throughput-oriented batch jobs

### Kernel optimization — GPU-level performance

- [gpu-architecture-fundamentals.md](references/kernel-optimization/gpu-architecture-fundamentals.md) — SMs, memory hierarchy, compute vs memory bound
- [kernel-optimization-for-llm-inference.md](references/kernel-optimization/kernel-optimization-for-llm-inference.md) — kernel-level techniques
- [kernel-optimization-tools.md](references/kernel-optimization/kernel-optimization-tools.md) — Triton, CUTLASS, torch.compile, profilers
- [flashattention.md](references/kernel-optimization/flashattention.md) — FlashAttention

### Infrastructure and operations

- [what-is-llm-inference-infrastructure.md](references/infrastructure-and-operations/what-is-llm-inference-infrastructure.md) — the serving stack
- [distributed-inference.md](references/infrastructure-and-operations/distributed-inference.md) — multi-GPU and multi-node serving
- [fast-scaling.md](references/infrastructure-and-operations/fast-scaling.md) — cold starts and autoscaling
- [comprehensive-observability.md](references/infrastructure-and-operations/comprehensive-observability.md) — metrics and monitoring for inference
- [multi-model-inference-pipelines.md](references/infrastructure-and-operations/multi-model-inference-pipelines.md) — compound AI pipelines
- [multi-cloud-and-cross-region-inference.md](references/infrastructure-and-operations/multi-cloud-and-cross-region-inference.md) — placement across clouds/regions
- [inferenceops-and-management.md](references/infrastructure-and-operations/inferenceops-and-management.md) — InferenceOps practices
- [build-and-maintenance-cost.md](references/infrastructure-and-operations/build-and-maintenance-cost.md) — cost of running your own stack

Section overview pages: each directory also has an `index.md` with a short
section summary.
