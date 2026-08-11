---
name: monitor
description: Use when the user asks to monitor, watch, track, or periodically check a running command, remote Job, CI run, deployment, publication, or other long-running objective. Starts the built-in Pi monitor workflow immediately in the current session and drives the objective autonomously, including routine recovery, until verified completion or a material blocker.
compatibility: Requires Pi Workflows and the built-in monitor workflow.
---

# Monitor

Use the built-in Pi `monitor` workflow as an autopilot for the requested objective. Monitoring is not passive status polling. The agent must maintain nominal operation, repair recoverable failures, resume durable work, and continue until the complete objective is verified or a material blocker makes safe continuation impossible.

A monitor request authorizes routine operational actions that are necessary to preserve and finish the stated objective. These actions include restarting or resuming the same Job or process, repairing an exact operational configuration or storage-path error, retrying transient infrastructure failures, restoring a verified checkpoint, and replacing a failed physical attempt with the same immutable execution contract. It does not authorize changing the objective, method, model, data source, production selection, or other consequential contract.

## Prepare and start without delay

As soon as the user invokes this skill:

1. Read the current conversation, active plan, repository instructions, and applicable compute, runtime, credential, deployment, or publication skills.
2. Preserve the exact objective, immutable execution contract, current identifiers, durable progress, cost already spent, approval ceilings, finish criteria, and known recovery rules in the workflow input. Write or update a durable plan or incident note first only when the work needs one for safe continuation.
3. Make the workflow instructions faithful to what the user requested. Do not reduce an implementation or recovery objective to observation-only monitoring.
4. Call `workflow` with `action: "start"` in the current Pi session without asking for another confirmation or waiting for a later turn.
5. Let the first workflow check run immediately. Do not use Unified Exec sleeps, manual polling loops, a second scheduler, or a separate Pi session as a substitute.

Do not finish the initiating turn before the workflow start call. If a safe contract cannot yet be written because a critical identifier or boundary is missing, gather it immediately when possible. Ask the user only when the missing decision is consequential and cannot be inferred safely.

## Build the monitor contract

Derive the workflow input from the full conversation:

- `task`: State the complete objective, the exact current target and stable identifiers, authoritative status sources, durable progress and final-output surfaces, approved recovery actions, immutable boundaries, cost and credential rules, and required validation or downstream operations.
- `everyMinutes`: Use the user's interval. Use `30` when the user gives no interval.
- `reportWhen`: Follow the user's request. Otherwise, report meaningful durable progress, recovery actions, state changes, failures, blocked states, cost risk, completion, and material ETA changes. Do not report repetitive unchanged checks unless the user asks for every check.
- `stopWhen`: Describe verified completion of the full objective, not the end of one physical process. Also name the material blockers that require human intervention.

When the conversation gives no clear finish criterion, set `stopWhen` to `Stop only when the user explicitly asks to stop.` Do not use that fallback when a broader implementation, repair, publication, or deployment objective is clear from context.

Do not invent a finite check count. Omit `maxChecks` unless the user explicitly requests one. The workflow host can apply its own safety upper bound. Disclose that bound if it appears.

## Default Hugging Face authority

For an objective that uses Hugging Face infrastructure, invoking this skill grants a default cumulative spending ceiling of **$1,000**, including all related attempts and money already spent, unless the conversation or repository sets a lower ceiling. This is a hard maximum, not a spending target.

Before launching or resuming paid work, load and follow the paid-compute, Hugging Face, Job-control, and runtime skills that apply. Measure or estimate cost, use the cheapest safe configuration, publish durable partial work, and enforce the cumulative ceiling in receipts or launch guards. Continue autonomously within the approved contract. Stop before the ceiling or when new evidence invalidates the approved estimate, method, hardware, or recovery assumptions.

The monitor may use a credential only when the conversation or repository has already authorized that credential's source, destination, and purpose. It may reuse that authorization for retries and replacement attempts under the same objective. It must not discover unrelated credentials, broaden scopes, copy credentials to a new store, or print secret values.

## Start the workflow

Start the built-in workflow in the current session with this shape:

```text
workflow({
  action: "start",
  workflow: "monitor",
  input: {
    task: "<complete objective, contract, recovery authority, and verification task>",
    everyMinutes: 30,
    reportWhen: "<derived reporting condition>",
    stopWhen: "<derived finish criterion or explicit-user-stop fallback>"
  }
})
```

Use the user-supplied interval instead of `30` when present. Add `maxChecks` only when the user explicitly supplies that limit.

Do not start a second monitor for the same objective while one is active. Update or replace the run only when the objective or contract changes. A replacement must preserve the previous accepted observation and durable recovery state.

## Complete workflow checks

Each workflow check arrives with an exact step contract. Apply the operational authority recorded in `task`. The default monitor contract is recovery-capable autopilot, not read-only observation.

For each check:

1. Query the target's authoritative status.
2. Query durable progress and final-output surfaces. Run independent reads in parallel when useful.
3. Compare the current values with the previous accepted observation.
4. If operation is not nominal, preserve evidence, diagnose the issue, apply the smallest authorized repair, and verify that durable progress resumes. Fix issues and restart Jobs or processes when that is necessary to keep the same objective moving.
5. Report absolute totals and meaningful deltas when counters matter.
6. Select the route that matches the contract:
   - `continue_quiet`: keep monitoring without a user report.
   - `continue_report`: report and keep monitoring.
   - `stop_quiet`: stop without a user report.
   - `stop_report`: report the final state and stop.
7. Call `workflow` with `action: "submit"` exactly once, using the supplied step and attempt IDs and the required output shape.

When the workflow requests a report acknowledgement, write only the requested concise user update, then submit the acknowledgement exactly as specified.

## Apply finish rules

### Still active

Continue. Keep reports short unless the state changed materially.

### Completed

Stop only after the inferred finish criterion is true. Verify required final artifacts, checksums, receipts, publication state, or downstream health before using `stop_report`.

### Failed, stopped, or blocked

Do not disarm the monitor for a superficial reason. One failed physical Job, command, CI run, deployment attempt, upload, or status read is not the end of the objective. Treat it as an operational event, preserve evidence and durable state, diagnose it, apply the smallest safe repair, restart or resume the same immutable contract, restore nominal operation, and keep monitoring.

Examples of recoverable conditions include transient provider or network errors, platform eviction, rate limits, expired physical attempts, safe checkpoint reconciliation, exact path or configuration mistakes, bounded storage failures, and a stalled deployment that has a documented recovery action.

Stop only for a material blocker, such as:

- a deterministic shared code or data defect that makes further attempts unsafe;
- an invalid, missing, or unverifiable checkpoint when useful state would be lost;
- a required credential that has no prior source-and-destination authorization;
- a changed model, method, source, hardware class, objective, or production decision;
- a destructive or security-sensitive action outside the recorded authority;
- a cost, time, or resource ceiling that cannot safely contain the remaining work;
- evidence that the requested result cannot be made truthful or valid under the current contract.

Never keep paid workers retrying a deterministic shared failure. Contain affected work, report the evidence and ETA impact, and stop for a decision.

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
