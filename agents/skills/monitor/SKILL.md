---
name: monitor
description: Use when the user asks to monitor, watch, track, or periodically check a running command, remote Job, CI run, deployment, publication, or other long-running task. Uses Unified Exec one-shot wake timers, checks immediately and every 30 minutes by default, reports meaningful deltas, and rearms until the target reaches a terminal state.
compatibility: Requires Unified Exec tools that support on_exit wake notifications. Monitoring lasts only while the current agent session can receive those notifications.
---

# Monitor

Monitor long-running work with one-shot Unified Exec wake timers. A request to monitor something authorizes periodic read-only checks and wake rearming. It does not authorize canceling, restarting, scaling, deploying, publishing, or changing the target unless the user says so explicitly.

## Establish the monitor contract

Before arming the timer, identify:

- The exact target and its stable identifier.
- The source of truth for status.
- Durable progress records such as receipts, checkpoints, manifests, or output files.
- The terminal success and failure states.
- Any follow-up actions the user has explicitly authorized.
- The check interval. Use 30 minutes when the user gives no interval.

Run the first check immediately. Do not wait 30 minutes before collecting the baseline.

For paid compute, load the applicable paid-compute and runtime skills before starting or continuing work. Monitoring does not expand a cost, time, hardware, retry, or method approval.

## Arm one one-shot wake

Use Unified Exec to start a sleep that exits once:

```text
exec_command({
  cmd: "sleep 1800",
  workdir: "<relevant working directory>",
  yield_time_ms: 1000,
  on_exit: "wake"
})
```

Convert a user-supplied interval to seconds. Record the returned session ID.

Use one-shot sleeps because `on_exit: "wake"` wakes the agent when the process exits. A perpetual shell loop wakes the agent only when the loop itself exits, so it cannot drive periodic checks.

Keep exactly one wake timer armed for a monitor. Do not create a system service, cron entry, scheduler installation, or always-on loop. Do not use `yield_until` for this pattern.

## Handle a wake notification

A Unified Exec completion notification is execution metadata. It does not replace the user's monitoring instruction. Continue the monitoring task instead of merely acknowledging the notification.

On every wake:

1. Drain the exited session with an empty `write_stdin` call when the session is still known. If it is no longer available, read its reported log path when output matters.
2. Query the target's authoritative status.
3. Query durable progress and final-output surfaces. Run independent checks in parallel.
4. Compare the new values with the prior check. Report absolute totals and meaningful deltas.
5. Apply the terminal-state rules below.

A sleep normally has no useful output, but the target checks still need to run after every wake.

## Terminal-state rules

### Still active

Rearm the next one-shot wake before sending the status update. Keep the update short unless something changed materially.

### Completed

Do not rearm. Verify the expected final artifacts, checksums, receipts, publication state, or downstream health before reporting completion. Continue any finalization steps only when they were part of the user's request or explicitly authorized.

### Failed, stopped, or blocked

Do not rearm automatic recovery unless the user already authorized that exact action under the current facts. Preserve durable work, inspect the failure evidence, and report the next safe action.

If a new defect, changed method, changed cost estimate, invalid backend, or other broken assumption appears, suspend any standing restart instruction and ask again. Never keep paid workers retrying a deterministic shared failure.

### Status unavailable

Retry only a cheap, bounded status read. If the source of truth remains unavailable, report the gap and rearm only when continued observation is still safe.

## Check the right surfaces

A useful monitor usually checks more than process state. Depending on the target, inspect:

- Process, Job, workflow, CI, or deployment status.
- Durable receipts and counters.
- Checkpoints or partial outputs.
- Final manifests, databases, publications, or release artifacts.
- Error state and the freshness of the last durable update.

Logs and progress counters alone do not prove saved work or completion. Prefer durable artifacts and authoritative remote state.

When counters matter, report the raw totals first. Examples include completed calls, reserved calls, rows, cost, tokens, units, artifacts, and remaining approved headroom. Do not infer that a metric is healthy merely because it is increasing.

## Handle conversation interruptions

The user may ask unrelated questions while a timer remains armed. Answer them without creating a second timer. The existing wake still owns the next check.

If a timer becomes stale because monitoring ended or the target changed, disarm it with `set_on_exit({ session_id, on_exit: "none" })` when the process should continue silently, or terminate it with `kill_session` when the sleep is no longer needed.

## Session boundary

This pattern is supervised monitoring tied to the current agent session. It does not guarantee checks while Pi or the host session is closed.

Unattended scheduling needs a durable controller host such as Pi Workflows. Installing or running that host persistently is a separate decision and requires explicit authorization.

## Status format

For an unchanged active target, prefer a compact report:

```text
Target remains running:
- Progress: <absolute total> (<delta since last check>)
- Cost or resource use: <total>
- Durable output: <state>
- Next check: <interval>
```

Explain anomalies, failures, or approval boundaries when they occur. Avoid repeating the full history at every check.
