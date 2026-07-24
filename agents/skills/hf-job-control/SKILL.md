---
name: hf-job-control
description: Use when designing, provisioning, integrating, or operating cooperative control for detached Hugging Face Jobs. Covers versioned lifecycle commands, bounded epoch changes, exact checkpoint resume, a private control dataset, content-addressed large payloads in an HF Bucket, and immutable applied-control receipts.
---

# HF Job Control

HF Job Control is a cooperative control protocol for detached Hugging Face Jobs.
The submitted program polls a private dataset at safe checkpoints and decides
whether to continue, pause, stop, or abort. Hugging Face does not mutate the
command or environment of a running Job.

Use this skill with the official `hf-cli` skill and the local `huggingface`
skill. Use `hf jobs` for compute, a private dataset for small desired-state
documents, and a private Bucket for large resume payloads.

## Default resources

On Onur's account, use these private resources unless the task names another
namespace:

```text
control dataset: osolmaz/jobs-control
artifact bucket: osolmaz/jobs-artifacts
```

The control dataset contains only small control documents, its schema, and its
README. Project repositories hold status, logs, and metrics. They also hold
predictions, submitted scripts, and final model artifacts. Large resumable state
belongs in the artifact Bucket.

Inspect both resources before creating or changing them:

```bash
hf datasets info osolmaz/jobs-control --format json
hf buckets info osolmaz/jobs-artifacts --format json
```

Create missing resources as private. Never replace an existing resource merely
because provisioning was requested:

```bash
hf repos create osolmaz/jobs-control --type dataset --private --exist-ok
hf buckets create osolmaz/jobs-artifacts --private --exist-ok
```

## Control boundary

A submitted Job has immutable hard limits in its checksummed script. A control
document may lower or restore a mutable limit within those bounds. It cannot
raise a hard limit, change a scientific selection rule, swap data, or change the
model.

Use these actions:

- `run` allows work to continue.
- `pause` saves an exact resume checkpoint at the next safe boundary and exits
  successfully with project status `paused`.
- `stop` finalizes at the next safe boundary. Use it only when the frozen
  experimental protocol authorizes operator-selected stopping.
- `abort` saves diagnostic state when possible, records failure, and exits with
  an error.

Prefer algorithmic early stopping for model selection. Human controls are for
operations. If a manual command changes the scientific outcome, update the plan
before issuing it and record that plan revision with the command.

## Control documents

Store one current document per run:

```text
controls/<run_id>.json
```

The v1 schema is in [references/control-v1.schema.json](references/control-v1.schema.json).
A minimal document is:

```json
{
  "schema_version": 1,
  "run_id": "teacher-base-search-v1",
  "generation": 1,
  "action": "run"
}
```

`generation` increases by one on every update. The optional `max_epochs` is a
soft runtime limit and must stay within the script's hard maximum. The optional
`resume_from` points to a content-addressed Bucket object.

Use the bundled publisher. Do not hand-edit the dataset:

```bash
uv run agents/skills/hf-job-control/scripts/job_control.py publish \
  --repo osolmaz/jobs-control \
  --run-id teacher-base-search-v1 \
  --action pause \
  --reason "Pause after the next safe checkpoint"
```

The publisher reads the current repository head, increments `generation`, and
creates a commit with `parent_commit` set. A concurrent update causes a conflict
instead of silently overwriting another command.

Inspect the exact current document with:

```bash
uv run agents/skills/hf-job-control/scripts/job_control.py show \
  --repo osolmaz/jobs-control \
  --run-id teacher-base-search-v1
```

The output includes the dataset revision and the control-file SHA-256. Never
infer either value from a later mutable head.

## Job integration

Poll only at a declared safe boundary, usually after evaluation and checkpoint
publication. A training loop should use this order:

1. Finish the current segment and evaluate the registered development surface.
2. Save the model and all state needed for an exact resume.
3. Publish the checkpoint and metrics along with structured project status.
4. Resolve the control dataset branch to a commit SHA.
5. Download `controls/<run_id>.json` from that exact revision.
6. Validate the schema and run ID. Then check the generation and action against
   the mutable limits.
7. Write an applied-control receipt before acting.

An exact resume checkpoint includes model weights, optimizer state, scheduler
state, Python and Torch RNG state, CUDA RNG state, global step, data-order
position, best-score state, and early-stopping counters. Record the submitted
script SHA-256 and the immutable input revisions beside it.

Reject a control when any of these conditions holds:

- Its `run_id` differs from the active run.
- Its generation is older than the last applied generation.
- It contains unknown fields or an unsupported schema version.
- A mutable limit exceeds the hard limit in the submitted script.
- A resume payload is missing, mutable, malformed, or fails size or SHA-256
  verification.

Seeing the same generation again is normal and produces no new action. A gap in
generation numbers is allowed because a Job may miss intermediate commands. It
applies the latest valid desired state and records that exact revision.

## Receipts and status

Copy every accepted control into the project's immutable run artifacts. Also
write an applied-control receipt following
[references/applied-control-v1.schema.json](references/applied-control-v1.schema.json).
The receipt identifies the control repository, exact revision, path, content
hash, generation, action, observation time, application time, and outcome.

The control dataset is desired state. It never becomes the source of run status.
The project artifact repository remains the source of observed state and final
provenance.

## Large artifacts

Hugging Face Buckets do not provide the control dataset's commit history. Treat
Bucket objects as immutable and content-address them:

```text
<program>/<run>/<kind>/sha256-<digest>/<filename>
```

Upload a new object for every changed payload. Never overwrite a key that has
already been published. A `resume_from` object records the Bucket, key, SHA-256,
and exact byte count. The Job verifies all four values before loading the
payload.

Final model weights should still be published to their model repository. The
Bucket is appropriate for bulky optimizer state, temporary resumable
checkpoints, and other large operational payloads. Record each important Bucket
object in the project's immutable manifest.

## Pause and resume

A detached HF Job cannot be resumed in place. On `pause`, the program finishes
its safe-boundary checkpoint, publishes status, and exits. A later launcher
starts a new Job with the same frozen script and an explicit checkpoint
revision or verified `resume_from` payload.

Run the construction and representation checks again after a code change. An
unchanged script may resume from exact state without repeating completed
training segments, provided the checkpoint verifier covers every state item
listed above.

Use `hf jobs cancel` only for emergencies. Cancellation may prevent a final
checkpoint and receipt from being written.

## Scheduler rules

A mutable search horizon requires a horizon-independent scheduler such as
ReduceLROnPlateau. Do not change the endpoint of a cosine or linear schedule
while it is running. A fixed-duration refit keeps its selected step count and
learning-rate trace immutable.

## Verification

Before launch, verify the control schema, initial control generation, private
resource settings, hard limits, safe polling boundary, and exact-resume test.
After each control action, verify the dataset commit, control hash, project
receipt, checkpoint hash, Job terminal state when applicable, and absence of
unintended changes to unrelated Jobs.

Before declaring a run complete, prove that every applied control has a receipt
and that every referenced Bucket object passes byte-count and SHA-256 checks.
