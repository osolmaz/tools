---
name: monitor
description: Use when the user asks to monitor, watch, track, or periodically check a running command, remote Job, CI run, deployment, publication, or other long-running task. Uses the built-in Pi monitor workflow, checks immediately and every 30 minutes by default, infers the finish criterion from the conversation, and continues without an agent-invented check limit when no finish criterion is clear.
compatibility: Requires Pi Workflows and the built-in monitor workflow.
---

# Monitor

Use the built-in Pi `monitor` workflow for periodic observation. A request to monitor something authorizes read-only checks. It does not authorize canceling, restarting, scaling, deploying, publishing, or changing the target unless the user explicitly says so.

## Build the monitor contract

Derive the workflow input from the conversation:

- `task`: Identify the exact target, its stable identifier, the authoritative status source, and the durable progress or final-output surfaces to inspect.
- `everyMinutes`: Use the user's interval. Use `30` when the user gives no interval.
- `reportWhen`: Follow the user's reporting request. Otherwise, report meaningful progress, state changes, failures, blocked states, completion, and important approval boundaries. Do not report repetitive unchanged checks unless the user asks for every check.
- `stopWhen`: Infer the finish criterion from the full conversation. Use the target's verified terminal success or failure state when that is the clear endpoint. Include required final artifacts, receipts, publication state, or downstream health when the request makes them part of completion.

Do not ask only because the finish criterion is unclear. When the conversation gives no clear finish criterion, set `stopWhen` to `Stop only when the user explicitly asks to stop.`

Do not invent a finite check count. Omit `maxChecks` unless the user explicitly requests a bounded number of checks. In particular, never add a small test limit such as two checks without the user's instruction. When `maxChecks` is omitted, do not claim that the run is mathematically infinite: the workflow host can apply its own safety upper bound. Disclose that bound if it appears.

Run the first check immediately through the workflow. The workflow then applies the requested interval.

For paid compute, load the applicable paid-compute and runtime skills before monitoring. Monitoring does not expand a cost, time, hardware, retry, or method approval.

## Start the workflow

Start the built-in workflow with this shape:

```text
workflow({
  action: "start",
  workflow: "monitor",
  input: {
    task: "<concrete observation task>",
    everyMinutes: 30,
    reportWhen: "<derived reporting condition>",
    stopWhen: "<derived finish criterion or explicit-user-stop fallback>"
  }
})
```

Use the user-supplied interval instead of `30` when present. Add `maxChecks` only when the user explicitly supplies that limit.

Do not start a second monitor for the same target while one is active. If the target or contract changes, cancel the old run before starting the replacement.

## Complete workflow checks

Each workflow check arrives with an exact step contract. Observe only unless the monitoring task explicitly authorizes a mutation.

For each check:

1. Query the target's authoritative status.
2. Query durable progress and final-output surfaces. Run independent reads in parallel when useful.
3. Compare the current values with the previous accepted observation.
4. Report absolute totals and meaningful deltas when counters matter.
5. Select the route that matches the contract:
   - `continue_quiet`: keep monitoring without a user report.
   - `continue_report`: report and keep monitoring.
   - `stop_quiet`: stop without a user report.
   - `stop_report`: report the final state and stop.
6. Call `workflow` with `action: "submit"` exactly once, using the supplied step and attempt IDs and the required output shape.

When the workflow requests a report acknowledgement, write only the requested concise user update, then submit the acknowledgement exactly as specified.

## Apply finish rules

### Still active

Continue. Keep reports short unless the state changed materially.

### Completed

Stop only after the inferred finish criterion is true. Verify required final artifacts, checksums, receipts, publication state, or downstream health before using `stop_report`.

### Failed, stopped, or blocked

Stop and report unless the conversation clearly defines that state as recoverable and continued observation is still useful. Do not restart or recover automatically unless the user already authorized that exact action under the current facts.

If a new defect, changed method, changed cost estimate, invalid backend, or other broken assumption appears, stop any automatic continuation that depended on the old assumption and ask again. Never keep paid workers retrying a deterministic shared failure.

### Status unavailable

Retry only a cheap, bounded status read. If the source remains unavailable, report the gap. Continue only when observation remains safe and the finish criterion is not met.

## Check the right surfaces

Depending on the target, inspect:

- Process, Job, workflow, CI, or deployment status.
- Durable receipts and counters.
- Checkpoints or partial outputs.
- Final manifests, databases, publications, or release artifacts.
- Error state and the freshness of the last durable update.

Logs and progress counters alone do not prove saved work or completion. Prefer durable artifacts and authoritative remote state.

## Stop on user request

When the user asks to stop, cancel the active monitor workflow with `workflow({ action: "cancel" })` and confirm that monitoring stopped. Do not wait for the next scheduled check.

## Status format

For an unchanged active target, prefer a compact report:

```text
Target remains running:
- Progress: <absolute total> (<delta since last report>)
- Cost or resource use: <total>
- Durable output: <state>
- Next check: <interval>
```

Explain anomalies, failures, or approval boundaries when they occur. Avoid repeating the full history at every check.
