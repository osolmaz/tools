---
name: huggingface-spaces
description: Operate, diagnose, and recover Hugging Face Spaces with the hf CLI, including build and startup monitoring, logs, visibility, restarts, and stuck queued or APP_STARTING deployments. Use when deploying to a Space, checking its runtime state, investigating a Space that is not serving the expected revision, or recovering a Space whose build or startup is not being picked up.
---

# Hugging Face Spaces

Use `hf spaces` for runtime state and logs. Keep repository changes, runtime
changes, and application health distinct so a healthy old revision is not
mistaken for a successful deployment.

## Inspect before changing state

1. Confirm the account and target:

   ```sh
   hf auth whoami
   hf spaces info OWNER/SPACE --format agent
   ```

2. Record the repository SHA, runtime SHA, stage, hardware, visibility, and Dev
   Mode state.
3. Read both build and run logs:

   ```sh
   hf spaces logs OWNER/SPACE --build --tail 120 --format agent
   hf spaces logs OWNER/SPACE --tail 200 --format agent
   ```

4. For an ordinary transition, wait instead of repeatedly restarting:

   ```sh
   hf spaces wait OWNER/SPACE --timeout 10m --format agent
   ```

Treat an unsigned `404` from a private Space as expected access control. Do not
diagnose it as an application route failure without an authenticated probe.

## Recover a deployment that is not picked up

Use a restart as the recovery action when all of the following are true:

- the desired repository SHA is already present;
- the stage remains transitional, such as `RUNNING_BUILDING` or
  `RUNNING_APP_STARTING`;
- build logs remain at `Build Queued`, or startup logs remain empty, across
  repeated checks for several minutes; and
- no builder, image pull, or application startup error is active.

Do not push an empty commit or rewrite the Space files. Restart the existing
revision once:

```sh
hf spaces restart OWNER/SPACE --format agent
hf spaces wait OWNER/SPACE --timeout 10m --format agent
```

This can cause Hugging Face to pick up an already-queued build or startup that
was otherwise stuck. It briefly interrupts the Space, so use it directly only
when the user asked to deploy, operate, or recover that Space. For a read-only
diagnosis, report the restart as the recommended action instead.

After the restart, verify rather than assuming success:

```sh
hf spaces info OWNER/SPACE --format agent
hf spaces logs OWNER/SPACE --build --tail 120 --format agent
hf spaces logs OWNER/SPACE --tail 200 --format agent
```

Require `RUNNING`, the intended runtime SHA, and application-specific health.
If the Space becomes `BUILD_ERROR` or `RUNTIME_ERROR`, stop restarting and
diagnose the first concrete error in the corresponding log.

## Dev Mode

Do not enable Dev Mode merely to inspect public logs. Enabling it changes live
runtime state and requires a registered Hugging Face SSH key for shell access.
If Dev Mode is used for an explicitly authorized diagnosis, disable it when
finished and wait for normal mode to return to `RUNNING`:

```sh
hf spaces dev-mode OWNER/SPACE --stop --format agent
hf spaces wait OWNER/SPACE --timeout 10m --format agent
```
