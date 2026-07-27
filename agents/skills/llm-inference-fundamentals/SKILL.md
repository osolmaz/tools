---
name: llm-inference-fundamentals
description: Unified domain knowledge and a reasoning workflow for LLM inference performance, benchmarking, capacity planning, and production serving. Use for TTFT, ITL, TPOT, throughput, goodput, prefill and decode, KV cache, batching, PagedAttention, prefix caching, speculative decoding, quantization, parallelism, GPU memory sizing, routing, autoscaling, observability, or inference infrastructure. Synthesizes separately pinned BentoML and Modular LLM inference handbooks without conflating their provenance.
license: See UPSTREAM.md
---

# LLM inference fundamentals

This skill combines the BentoML and Modular LLM inference handbooks into one
operating model. It does not overwrite one source with the other.

## Source boundary

The source text remains separated by publisher and snapshot:

- [BentoML edition](references/bentoml/introduction.md), pinned at
  `ea07b2ccd9b35db810763fc76980b26be1d2b871`
- [Modular edition](references/modular/index.md), pinned at
  `317b9816ec3080031333ed9ee44dfce919763bf7`

BentoML joined Modular through an acquisition announced on 2026-02-10, and the
snapshots share Git history. They still remain separately attributed editions
because their branding and contents differ. Corporate ownership does not erase
those source boundaries.
[UPSTREAM.md](UPSTREAM.md) records the relationship, repositories, licenses,
transformations and update commands.

Use this file for the merged reasoning workflow. Open the paired source pages
when a question needs derivations, diagrams, implementation detail, historical
context, or exact attribution.

## Source reconciliation

For a topic covered by both editions, start with the newer Modular treatment and
check the BentoML treatment before making a broad claim. The older edition may
retain useful material that was removed or reframed later. If the editions
differ, state the difference and identify the snapshot. Do not silently choose
one.

Treat vendor-specific tools, products, performance claims, and deployment advice
as examples from that publisher. Do not turn them into engine-neutral facts.
When quoting text, attribute the individual edition. Do not attribute a quote
to this skill.

The Modular edition adds substantial treatment of attention, causal masking and
KV-cache mechanics. It also expands prefix-caching examples and speculative
methods such as Medusa, MTP, n-gram speculation, and EAGLE. The BentoML snapshot
retains earlier material such as hybrid cloud overflow guidance and its original
tool examples. Both remain available in the paired corpus.

## Working model

An inference request passes through admission and queueing, tokenization,
prefill, autoregressive decode, serialization plus transport. Prefill processes
the prompt in parallel and populates the KV cache. Ordinary decode generates one
token at a time while reading the active sequence's KV state.

Keep the deployed artifact separate from the abstract model. Weight format,
weight quantization, KV precision, tokenizer, kernels, inference engine, and
speculative draft are parts of the deployed stack. A comparison that changes
several of these is a stack comparison. It does not isolate the engine or the
quantization choice.

A server's maximum context length is capacity. Decode work depends on the tokens
actually resident in active sequences. Do not treat configured capacity as the
active workload.

Keep evidence classes explicit:

- A **measurement** comes from completed requests under a declared workload.
- An **estimate** applies a formula or extrapolation to stated inputs.
- A **ceiling** is a physical or architectural upper bound. It does not predict
  an end-to-end benchmark.

## Benchmark contract

Before interpreting a result, capture enough state to reproduce the work and the
measurement boundary.

1. Record the exact model artifact, tokenizer, weight and KV formats, engine
   revision and launch command. Include the kernels and hardware.
2. Declare prompt length, requested and completed output length, request count,
   concurrency, sampling parameters, and stopping behavior.
3. State whether prefixes and kernels were cold, warm, reused, or cleared.
   Record the graph-capture state too. Fresh-prefill tests require distinct
   uncached prefixes.
4. Preserve per-request latency distributions as well as aggregate throughput.
   Aggregate tokens per second can rise while each session becomes slower.
5. For speculative decoding, retain proposed and accepted draft tokens,
   acceptance length or rate, target verification traffic, and rejected work.
6. Keep every valid sample and declare the aggregation rule. Exclude a sample
   only for a recorded safety, correctness, or instrumentation failure.

Use outputs long enough to reach steady decode before making sustained-speed
claims. Content-dependent methods need multiple distinct semantic prompts.

## Metric rules

Use the paired metric references from
[BentoML](references/bentoml/llm-inference-basics/llm-inference-metrics.md) and
[Modular](references/modular/llm-inference-basics/llm-inference-metrics.md).
Always name the observation point.

- **TTFT** spans request arrival through delivery of the first output token.
  Client-observed TTFT can include queueing, tokenization, scheduling, prefill,
  first-token decode, serialization plus transport.
- **TPOT** is often calculated as
  `(end-to-end latency - TTFT) / (completed output tokens - 1)`. Report the
  actual denominator and whether the first token is excluded.
- **ITL** measures intervals between streamed tokens. Its distribution reveals
  stalls that a mean TPOT can hide.
- **Throughput** is completed work per unit time. State whether it counts input,
  output, or all tokens and whether the number is aggregate or per session.
- **Goodput** counts requests that meet declared latency SLOs. It is preferable
  to raw throughput when late requests are not useful service.
- **Effective prefill throughput** computed as prompt tokens divided by TTFT is
  an end-to-end ratio. It is not interchangeable with a kernel or rolling-server
  prefill metric.

Prefix reuse changes prefill work, so label warmed-prefix results as cache hits.
Speculative decode ordinarily begins after target prefill and does not explain a
lower fresh-prefix TTFT.

## Capacity and optimization sequence

Account for model weights, KV cache, runtime workspaces, graph captures,
allocator headroom, and non-model host memory. KV demand scales with active
sequence length and concurrency. Weight quantization and KV-cache quantization
are independent choices.

Tune in this order:

1. Prove correct model loading and output while memory and process safeguards
   remain active.
2. Freeze a representative workload, measurement boundary, and aggregation
   rule.
3. Measure a plain baseline before adding cache reuse, speculative decoding,
   disaggregation, or offloading.
4. Change one major dimension at a time and recheck correctness, memory
   headroom, TTFT, ITL, per-session speed, aggregate throughput, and goodput.
5. Raise concurrency or context capacity only while the selected SLO and memory
   floor continue to hold.

Use batching and continuous scheduling to improve utilization before assuming
that model compute is the only bottleneck. Use PagedAttention to manage KV
fragmentation, prefix caching only where reuse exists, speculation only where
acceptance repays draft and verification work, and parallelism only after
including communication cost. Scaling decisions should follow measured demand,
queue behavior, cold-start time, placement constraints, and failure domains.

## Paired topic routes

| Question | BentoML source | Modular source |
| --- | --- | --- |
| How inference, attention and generation phases work | [Inference mechanics](references/bentoml/llm-inference-basics/how-does-llm-inference-work.md) | [Expanded inference mechanics](references/modular/llm-inference-basics/how-does-llm-inference-work.md) |
| How to define latency/throughput/goodput | [Metrics](references/bentoml/llm-inference-basics/llm-inference-metrics.md) | [Metrics](references/modular/llm-inference-basics/llm-inference-metrics.md) |
| How to design or interpret a benchmark | [Benchmarking](references/bentoml/inference-optimization/llm-performance-benchmarks.md) | [Benchmarking](references/modular/inference-optimization/llm-performance-benchmarks.md) |
| How to size weights and KV memory | [Memory sizing](references/bentoml/getting-started/calculating-gpu-memory-for-llms.md) | [Memory sizing](references/modular/getting-started/calculating-gpu-memory-for-llms.md) |
| How batching and chunked prefill behave | [Batching](references/bentoml/inference-optimization/static-dynamic-continuous-batching.md) | [Batching](references/modular/inference-optimization/static-dynamic-continuous-batching.md) |
| When prefix caching helps | [Prefix caching](references/bentoml/inference-optimization/prefix-caching.md) | [Expanded prefix examples](references/modular/inference-optimization/prefix-caching.md) |
| How to evaluate speculative decoding | [Speculative decoding](references/bentoml/inference-optimization/speculative-decoding.md) | [Expanded speculative methods](references/modular/inference-optimization/speculative-decoding.md) |
| How to choose parallelism | [Parallelism](references/bentoml/inference-optimization/data-tensor-pipeline-expert-hybrid-parallelism.md) | [Parallelism](references/modular/inference-optimization/data-tensor-pipeline-expert-hybrid-parallelism.md) |
| How GPU architecture and kernels affect speed | [GPU fundamentals](references/bentoml/kernel-optimization/gpu-architecture-fundamentals.md) | [GPU fundamentals](references/modular/kernel-optimization/gpu-architecture-fundamentals.md) |
| How to plan routing, scaling and observability | [Infrastructure](references/bentoml/infrastructure-and-operations/what-is-llm-inference-infrastructure.md) | [Infrastructure](references/modular/infrastructure-and-operations/what-is-llm-inference-infrastructure.md) |
| How hosted, BYOC, hybrid and on-prem options differ | [Deployment guidance](references/bentoml/getting-started/serverless-vs-self-hosted-llm-inference.md) | [Deployment guidance](references/modular/getting-started/serverless-vs-self-hosted-llm-inference.md) |

The complete two-source map and license provenance are in
[references/README.md](references/README.md). Each source directory preserves
its own section indexes and internal links.
