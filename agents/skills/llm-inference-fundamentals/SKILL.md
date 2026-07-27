---
name: llm-inference-fundamentals
description: Domain knowledge and a reasoning workflow for LLM inference performance, benchmarking, capacity planning, and production serving. Use for TTFT, ITL, TPOT, throughput, goodput, prefill and decode, KV cache, batching, PagedAttention, prefix caching, speculative decoding, quantization, parallelism, GPU memory sizing, routing, autoscaling, observability, or inference infrastructure. Bundles a pinned plain-Markdown edition of Modular's LLM Inference Handbook.
license: See UPSTREAM.md
---

# LLM inference fundamentals

This skill is a reasoning and navigation layer over Modular's
*LLM Inference Handbook*. The handbook is vendored under
[references/index.md](references/index.md) so the underlying explanations
remain available without relying on a live website.

The Modular repository continues the Git history of the earlier BentoML
handbook that this skill bundled. The current snapshot replaces that older
snapshot in place. [UPSTREAM.md](UPSTREAM.md) records the source revision,
license, attribution, lineage, and mechanical Markdown changes.

## Working method

Read only the references needed for the question. Most tasks need one overview
and one detailed page.

Before reasoning from a benchmark or recommending a configuration, write down
the workload and deployed stack. Capture the model and artifact, weight and KV
precision, inference engine and revision, kernels, hardware, prompt and output
lengths, concurrency, batching, cache state, and speculative-decoding settings.
A comparison that changes several of these is a deployed-stack comparison.

Keep three kinds of statements separate:

- A **measurement** comes from a completed request or benchmark with a declared
  workload.
- An **estimate** applies a formula or extrapolation to stated inputs.
- A **ceiling** is a physical or architectural upper bound. It does not predict
  an end-to-end benchmark by itself.

If the evidence does not identify a required field, say that it is unknown.
Avoid filling missing benchmark details with engine defaults because defaults
change across releases and hardware.

## Benchmark contract

A useful inference benchmark records enough detail to reproduce both the work
and the metric.

1. Identify the exact model artifact, quantization, tokenizer, engine revision
   and command. Record the hardware as part of the same configuration.
2. Declare prompt length, requested and completed output length, request count,
   concurrency, sampling parameters, and stopping behavior.
3. State whether prefixes and kernels were cold, warm, reused, or explicitly
   cleared. Fresh-prefill claims require distinct uncached prefixes.
4. Report per-request latency distributions alongside aggregate throughput.
   Aggregate tokens per second can rise while each request becomes slower.
5. For speculative decoding, retain accepted and proposed draft-token counts,
   acceptance length or rate, target verification work, and rejected work.
6. Preserve every valid sample and declare the aggregation rule. Exclude a
   sample only for a recorded correctness, safety, or instrumentation failure.

Use enough generated tokens to reach steady decode when making sustained-speed
claims. Short outputs overemphasize startup and scheduling costs as well as
first-token work.
Content-dependent methods such as speculative decoding need several distinct
semantic prompts.

## Metric rules

Use the definitions in
[LLM inference metrics](references/llm-inference-basics/llm-inference-metrics.md)
and keep the measurement boundary explicit.

- **TTFT** spans request arrival through delivery of the first output token.
  Client-observed TTFT includes queueing, tokenization, scheduling and prefill.
  It also includes first-token decode, serialization and transport unless
  instrumentation removes some of them.
- **TPOT** is commonly computed as
  `(end-to-end latency - TTFT) / (completed output tokens - 1)`. State the exact
  denominator and whether the first token is excluded.
- **ITL** is the interval between streamed tokens. Its distribution exposes
  stalls that a mean TPOT can hide.
- **Throughput** is completed work per unit time. Report whether token
  throughput counts input tokens, output tokens, or both, and whether it is an
  aggregate or per-session value.
- **Goodput** counts only requests that satisfy the declared latency SLOs. It is
  the right capacity metric when slow requests do not count as useful service.
- **Effective prefill throughput** derived from prompt tokens divided by TTFT is
  an end-to-end ratio. Kernel prefill throughput and rolling server metrics use
  different boundaries.

Prefix caching changes prefill work. A warmed-prefix result should be labeled as
cache reuse. Speculative decoding starts after target prefill, so it does not
explain a lower fresh-prefix TTFT.

## Capacity and tuning sequence

Tune in an order that keeps each result interpretable.

1. Prove that the model loads and returns correct output with memory and process
   safeguards active.
2. Account for weights, KV cache, runtime workspaces, graph captures, allocator
   headroom, and non-model host memory.
3. Freeze a representative workload and the metric aggregation rule.
4. Measure a plain baseline before enabling caching, speculation,
   disaggregation, or offloading.
5. Change one major dimension at a time. Recheck correctness, memory headroom,
   TTFT, ITL, per-request throughput, aggregate throughput, and goodput.
6. Increase concurrency or context capacity only while the chosen SLO and
   memory floor still hold.

A server's maximum context length is capacity. Decode cost follows the tokens
actually resident in each active sequence's KV cache. Weight quantization and
KV-cache quantization are separate choices. Format names such as GGUF and GPTQ,
along with AWQ, FP8 or NVFP4, identify different artifacts and kernel paths.

## Topic routes

| Task | Start with | Then read |
| --- | --- | --- |
| Define or interpret latency and throughput | [Metrics](references/llm-inference-basics/llm-inference-metrics.md) | [Benchmarking](references/inference-optimization/llm-performance-benchmarks.md) |
| Diagnose prefill, decode, attention, or KV behavior | [Inference mechanics](references/llm-inference-basics/how-does-llm-inference-work.md) | [GPU fundamentals](references/kernel-optimization/gpu-architecture-fundamentals.md) |
| Size a model and context window | [GPU memory calculation](references/getting-started/calculating-gpu-memory-for-llms.md) | [Quantization](references/model-preparation/llm-quantization.md) and [KV offloading](references/inference-optimization/kv-cache-offloading.md) |
| Tune batching and scheduling | [Batching](references/inference-optimization/static-dynamic-continuous-batching.md) | [PagedAttention](references/inference-optimization/pagedattention.md) and [routing](references/inference-optimization/inference-routing.md) |
| Evaluate prefix reuse | [Prefix caching](references/inference-optimization/prefix-caching.md) | [Routing](references/inference-optimization/inference-routing.md) |
| Evaluate speculative decoding | [Speculative decoding](references/inference-optimization/speculative-decoding.md) | [Benchmarking](references/inference-optimization/llm-performance-benchmarks.md) |
| Choose an engine or accelerator | [Framework selection](references/getting-started/choosing-the-right-inference-framework.md) | [GPU selection](references/getting-started/choosing-the-right-gpu.md) |
| Plan multi-GPU or multi-node serving | [Parallelism](references/inference-optimization/data-tensor-pipeline-expert-hybrid-parallelism.md) | [Distributed inference](references/infrastructure-and-operations/distributed-inference.md) |
| Separate prefill and decode fleets | [Prefill-decode disaggregation](references/inference-optimization/prefill-decode-disaggregation.md) | [Routing](references/inference-optimization/inference-routing.md) and [observability](references/infrastructure-and-operations/comprehensive-observability.md) |
| Plan production scaling and operations | [Infrastructure](references/infrastructure-and-operations/what-is-llm-inference-infrastructure.md) | [Fast scaling](references/infrastructure-and-operations/fast-scaling.md), [observability](references/infrastructure-and-operations/comprehensive-observability.md), and [InferenceOps](references/infrastructure-and-operations/inferenceops-and-management.md) |
| Compare hosted/BYOC/on-prem deployment | [Hosted versus self-hosted](references/getting-started/serverless-vs-self-hosted-llm-inference.md) | [BYOC](references/getting-started/bring-your-own-cloud.md), [on-prem](references/getting-started/on-prem-llms.md), and [cost](references/infrastructure-and-operations/build-and-maintenance-cost.md) |

For broad orientation, start with the
[handbook introduction](references/index.md).

## Reference catalog

### Inference basics

- [What LLM inference is](references/llm-inference-basics/what-is-llm-inference.md)
- [Inference mechanics](references/llm-inference-basics/how-does-llm-inference-work.md)
- [Metrics and SLOs](references/llm-inference-basics/llm-inference-metrics.md)
- [Training and inference differences](references/llm-inference-basics/training-inference-differences.md)
- [CPU/GPU/TPU comparison](references/llm-inference-basics/cpu-vs-gpu-vs-tpu.md)

### Deployment planning

- [Model selection](references/getting-started/choosing-the-right-model.md)
- [Inference framework selection](references/getting-started/choosing-the-right-inference-framework.md)
- [GPU selection](references/getting-started/choosing-the-right-gpu.md)
- [GPU memory calculation](references/getting-started/calculating-gpu-memory-for-llms.md)
- [Hosted and self-hosted inference](references/getting-started/serverless-vs-self-hosted-llm-inference.md)
- [On-prem inference](references/getting-started/on-prem-llms.md)
- [Bring your own cloud](references/getting-started/bring-your-own-cloud.md)

### Model preparation

- [Quantization](references/model-preparation/llm-quantization.md)
- [Fine-tuning](references/model-preparation/llm-fine-tuning.md)
- [Distillation](references/model-preparation/llm-distillation.md)

### Request and API behavior

- [OpenAI-compatible APIs](references/model-interaction/openai-compatible-api.md)
- [Anthropic-compatible APIs](references/model-interaction/anthropic-compatible-api.md)
- [Inference parameters](references/model-interaction/inference-parameters.md)
- [Prompt engineering](references/model-interaction/prompt-engineering.md)
- [Function calling](references/model-interaction/function-calling.md)
- [Structured outputs](references/model-interaction/structured-outputs.md)
- [Model Context Protocol](references/model-interaction/model-context-protocol.md)

### Inference optimization

- [Benchmarking](references/inference-optimization/llm-performance-benchmarks.md)
- [Batching and chunked prefill](references/inference-optimization/static-dynamic-continuous-batching.md)
- [PagedAttention](references/inference-optimization/pagedattention.md)
- [Prefix caching](references/inference-optimization/prefix-caching.md)
- [KV-cache offloading](references/inference-optimization/kv-cache-offloading.md)
- [Speculative decoding](references/inference-optimization/speculative-decoding.md)
- [Prefill-decode disaggregation](references/inference-optimization/prefill-decode-disaggregation.md)
- [Parallelism](references/inference-optimization/data-tensor-pipeline-expert-hybrid-parallelism.md)
- [Inference routing](references/inference-optimization/inference-routing.md)
- [Offline batch inference](references/inference-optimization/offline-batch-inference.md)

### Kernels and GPU execution

- [GPU architecture fundamentals](references/kernel-optimization/gpu-architecture-fundamentals.md)
- [Kernel optimization](references/kernel-optimization/kernel-optimization-for-llm-inference.md)
- [Kernel tools](references/kernel-optimization/kernel-optimization-tools.md)
- [FlashAttention](references/kernel-optimization/flashattention.md)

### Infrastructure and operations

- [Inference infrastructure](references/infrastructure-and-operations/what-is-llm-inference-infrastructure.md)
- [Distributed inference](references/infrastructure-and-operations/distributed-inference.md)
- [Fast scaling](references/infrastructure-and-operations/fast-scaling.md)
- [Observability](references/infrastructure-and-operations/comprehensive-observability.md)
- [Multi-model pipelines](references/infrastructure-and-operations/multi-model-inference-pipelines.md)
- [Multi-cloud and cross-region inference](references/infrastructure-and-operations/multi-cloud-and-cross-region-inference.md)
- [InferenceOps](references/infrastructure-and-operations/inferenceops-and-management.md)
- [Build and maintenance cost](references/infrastructure-and-operations/build-and-maintenance-cost.md)

Each topic directory also contains an `index.md` with its upstream section
summary. Interactive calculators and visualizers remain on the rendered
handbook and are linked from the corresponding vendored pages.
