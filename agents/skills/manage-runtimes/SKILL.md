---
name: manage-runtimes
description: Use when creating, updating, selecting, promoting, auditing, or deleting local runtime environments for inference engines or benchmark toolchains such as vLLM, SGLang, llama.cpp, TensorRT-LLM, or FlashInfer-backed runtimes. Enforces canonical runtime paths, manifests, smoke tests, promotion rules, cleanup rules, and prevents ad hoc virtualenv or toolchain sprawl.
---

# Manage Runtimes

## Core Rule

Use canonical runtime roots instead of scratch, service, or repo-local environments.

Default layout:

```text
~/runtimes/<engine>/
  current -> versions/<runtime-name>
  versions/
    <runtime-name>/
      .venv/                 # only for Python runtimes
      manifest.json
      notes.md
      smoke.json
  profiles/
    <profile-name>.json
```

For vLLM, use:

```text
~/runtimes/vllm/current/.venv/bin/vllm
```

Do not create new inference runtime environments under `~/scratch`, `~/services`, `~/repos`, or project-local `.venv` directories unless the user explicitly approves a one-off exception.

## Runtime Names

Name runtime versions by engine, version, purpose, and important hardware/backend traits:

```text
vllm-0.23.1-qwen36-sm121-flashinfer
vllm-0.23.1-qwen36-sm121-triton-safe
sglang-0.5.2-blackwell-cu130
llama-cpp-b6100-cuda-cu130
```

Prefer names that explain why the runtime exists. Avoid vague names like `test`, `latest`, `new`, or `scratch`.

## Manifest

Every promoted or candidate runtime must have `manifest.json`.

Minimum fields:

```json
{
  "name": "vllm-0.23.1-qwen36-sm121-flashinfer",
  "engine": "vllm",
  "status": "candidate",
  "created_at": "2026-07-01",
  "runtime_path": "/home/bob/runtimes/vllm/versions/vllm-0.23.1-qwen36-sm121-flashinfer",
  "executable": "/home/bob/runtimes/vllm/current/.venv/bin/vllm",
  "versions": {
    "python": "3.12",
    "vllm": "0.23.1rc1",
    "torch": "2.11.0+cu130",
    "cuda": "13.0",
    "flashinfer": "0.6.13"
  },
  "hardware": {
    "cuda_arch": "sm_121",
    "flashinfer_cubins": ["sm121"]
  },
  "source": {
    "repo": "https://github.com/vllm-project/vllm",
    "commit": ""
  },
  "smoke_tests": [],
  "notes": ""
}
```

Use `status` values:

- `candidate`: created but not trusted yet
- `working`: smoke-tested and safe to use
- `archived`: kept for reproducibility, not the default
- `broken`: known bad, kept only for debugging

## Profiles

Keep model-specific serve flags in `profiles/`, not scattered through benchmark specs.

Profile example:

```json
{
  "name": "qwen36-35b-nvfp4-spark",
  "model": "nvidia/Qwen3.6-35B-A3B-NVFP4",
  "runtime": "vllm-0.23.1-qwen36-sm121-flashinfer",
  "env": {
    "CUTE_DSL_ARCH": "sm_121a",
    "FLASHINFER_DISABLE_VERSION_CHECK": "1"
  },
  "serve_args": {
    "quantization": "modelopt",
    "load_format": "fastsafetensors",
    "kv_cache_dtype": "fp8",
    "attention_backend": "flashinfer",
    "moe_backend": "marlin",
    "max_num_batched_tokens": 8192
  },
  "status": "candidate",
  "last_smoke_test": null
}
```

Benchmark specs should describe workload shape: prompt length, output length, request rate, concurrency, repeats, and result location. They should reference the canonical runtime/profile instead of carrying unrelated toolchain decisions inline.

## Workflow

1. Audit existing runtimes before creating anything new.
2. Report expected disk impact before creating, replacing, or deleting a runtime.
3. Create new runtimes only under `~/runtimes/<engine>/versions/<runtime-name>/`.
4. Write or update `manifest.json` during setup, not after the fact.
5. Run a smoke test before promoting a runtime.
6. Promote by updating `current` only after the smoke test passes.
7. Mark superseded runtimes as `archived` or `broken` in their manifest.
8. Delete old runtimes only when the user explicitly asks or confirms cleanup.

Before starting any local inference server, compiler-heavy model load, or
benchmark traffic, also use `$safe-inference-launch`. Do not launch vLLM,
llama.cpp, SGLang, TensorRT-LLM, FlashInfer/modelopt, Ollama, or similar local
serving processes directly.

When promoting a local runtime, install automatic guarded shims for the runtime
entrypoint if possible. For vLLM this means wrapping the promoted executable:

```bash
~/.codex/skills/safe-inference-launch/scripts/install-shims.sh \
  --wrap ~/runtimes/vllm/current/.venv/bin/vllm
```

This protects benchmark scripts that call the runtime by absolute path.

## Smoke Tests

Use the smallest test that proves the runtime can start, serve, and return output without exceeding safety limits.

For vLLM benchmark runtimes:

- verify the executable version,
- verify import paths for key packages,
- verify hardware-specific packages such as FlashInfer cubins,
- run one low-risk request,
- save the exact command and result in `smoke.json`.

Do not promote a runtime based only on successful package installation.

## Safety

- Do not lower memory guards just to get a smoke test to pass.
- Do not start local inference as a fallback when the intended target is a
  remote endpoint or hosted API. Verify the remote target first and report auth
  or availability failures.
- Use a process-group watchdog plus active earlyoom for local large-model
  launches. If those guards are unavailable, refuse the launch or ask before
  continuing.
- Do not create system or user services unless the user explicitly asks for a service.
- Do not treat `~/services` as a runtime location.
- Do not mutate an existing working runtime in place. Create a new versioned runtime and promote it after testing.
- Preserve old runtime manifests when cleaning up so results remain explainable.
