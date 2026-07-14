---
name: huggingface
description: Onur Solmaz's personal Hugging Face tips and tricks. Use for any Hugging Face task alongside the relevant official Hugging Face marketplace skills, especially when personal operating conventions, deployment lessons, or recovery notes may apply. This skill supplements rather than replaces Hugging Face's published skills.
---

# Hugging Face

Treat this as Onur's personal overlay for Hugging Face work. Apply it together
with the relevant Hugging Face-published skills. Keep official product workflows
in the official skills and keep only Onur's additional preferences and learned
operational remedies here.

## Work alongside the published skills

Discover the current Hugging Face marketplace catalog instead of assuming a
fixed list:

```sh
hf skills list --format json
```

Use every installed official skill that materially covers the task. Typical
routing includes `hf-cli` for Hub operations and task-specific skills for
Spaces, datasets, Gradio, papers, local models, training, evaluations, Trackio,
ZeroGPU, tool building, and cloud deployment. The marketplace is the source of
truth when names or coverage change.

If a matching official skill is unavailable locally, install or update the
published copy through `hf skills`; do not duplicate its contents here:

```sh
hf skills add SKILL_NAME
hf skills update SKILL_NAME
```

Choose project or global installation deliberately. Do not silently overwrite
a locally modified skill with `--force`.

## Personal tips and tricks

### Recover a Space deployment that is not picked up

Before changing state, inspect the Space and both log streams:

```sh
hf auth whoami
hf spaces info OWNER/SPACE --format agent
hf spaces logs OWNER/SPACE --build --tail 120 --format agent
hf spaces logs OWNER/SPACE --tail 200 --format agent
hf spaces wait OWNER/SPACE --timeout 10m --format agent
```

Use a restart as the recovery action when all of the following are true:

- the intended repository SHA is already present;
- the stage remains transitional, such as `RUNNING_BUILDING` or
  `RUNNING_APP_STARTING`;
- build logs remain at `Build Queued`, or startup logs remain empty, across
  repeated checks for several minutes; and
- no builder, image-pull, or application-startup error is active.

Restart the existing revision once:

```sh
hf spaces restart OWNER/SPACE --format agent
hf spaces wait OWNER/SPACE --timeout 10m --format agent
```

This can make Hugging Face pick up an already-queued build or startup. Do not
push an empty commit, rewrite Space files, or repeatedly restart it. A restart
briefly interrupts the Space, so perform it directly only when the user asked
to deploy, operate, or recover that Space. For read-only diagnosis, report it
as the recommended remedy.

Afterward, require `RUNNING`, the intended runtime SHA, and
application-specific health. If the Space reaches `BUILD_ERROR` or
`RUNTIME_ERROR`, stop restarting and diagnose the first concrete error in the
corresponding log.

### Distinguish Hub access from application failures

A private Space returns an unsigned `404` by design. Do not treat that alone as
an application routing failure. Use an authenticated or signed probe, then
separately verify the repository SHA, runtime SHA, stage, build logs, run logs,
and application health.

### Clean up Dev Mode

Do not enable Dev Mode merely to read public logs. It changes live runtime
state, and SSH access also requires a registered Hugging Face SSH key. When an
explicitly authorized diagnosis uses Dev Mode, disable it afterward and wait
for normal mode to return to `RUNNING`:

```sh
hf spaces dev-mode OWNER/SPACE --stop --format agent
hf spaces wait OWNER/SPACE --timeout 10m --format agent
```

If the return to normal mode stalls at `RUNNING_APP_STARTING` with empty logs,
apply the one-time restart remedy above.

## Maintaining this overlay

Add a tip here only when Onur explicitly asks to remember it or a repeated
workflow establishes it as a personal convention. Keep each tip concrete,
actionable, and narrower than the official skill it supplements.
