## Sherlock Holmes Mode for Review / Incident

Credit: Frank Y (@frankekn)

When the user asks for a review, incident investigation, abnormal-
behavior investigation, root-cause analysis, or explicitly says
`Sherlock Holmes mode` / `investigate like Sherlock Holmes`, enable
this mode. Do not stop at the first plausible cause; connect the user-
visible behavior, runtime mechanism, durable state, parallel tasks, and
falsifying evidence.

- Reconstruct the user-visible timeline first: exact timestamp, actor/
source, visible output, and corresponding durable state change.
- Trace from entrypoint to output: entrypoint -> callsite -> state
mutation -> notification/output. Do not describe the cause as an
unverifiable phrase like "state management issue."
- Every root-cause claim must include:
  - **Mechanism**: which code path / runtime rule made it happen.
  - **Witness**: file/line, log row, DB row, command output, session
transcript, or other re-checkable evidence.
  - **Definition + callsite**: where the behavior is defined and where
it was invoked this time.
  - **Counter-test**: which alternative explanations were checked and
ruled out.
  - **Severity**: user impact, recurrence, data-integrity risk, and
whether state was preserved, restored, overwritten, or lost.
- When protected state, queues, retries, callbacks, workers, cron,
background tasks, or multiple agents are involved, check overlapping
time windows and parallel writers before blaming a single agent.
- Clearly separate symptom, trigger, root cause, and contributing
factors; do not merge them into one vague explanation.
- Do not claim that an agent/model violated a contract without evidence
from the exact tool call, write path, DB mutation, or returned payload.
- If new evidence overturns an earlier hypothesis, explicitly correct
the hypothesis.
- Final reports must be actionable: list P0/P1/P2 fixes and identify
which fix reduces user-visible harm fastest.

A review or incident investigation must answer at least:

1. What did the user actually see?
2. Which durable records prove it happened?
3. Which code path produced each visible message or state change?
4. What worker / queue / session / cron was running at the same time?
5. Which hypotheses were ruled out?
6. What is the smallest safe fix?
7. What regression test would prevent this from happening again?
