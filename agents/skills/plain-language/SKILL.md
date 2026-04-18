---
name: plain-language
description: Use when the user asks for a plainer, simpler, shorter, or more direct explanation. Produces concrete, full-sentence explanations that lead with the main point, avoid jargon, and use exact numbers when they matter.
---

# Plain Language

When this skill is invoked, explain the idea in the simplest correct way you can.

Write like a strong engineer speaking plainly:

- short full sentences
- main point first
- concrete words
- no jargon unless it is required
- no extra framework unless the user asked for depth

If the user says `plainer`, `shorter`, `full sentences`, or `plain language`, remove another layer of abstraction.

Bad:

- "The current bottleneck is scheduler-level preemption caused by shared dirty-state semantics."

Plain:

- "The main problem is that the system keeps choosing to scan the repo again instead of continuing to fill the missing PRs."

Bad:

- "The remaining failures are caused by control-plane contention across a shared database pool."

Plain:

- "The real problem is that the repo scan, webhook jobs, and queue system are all sharing the same small database connection pool, so they slow each other down and start timing out."

Bad:

- "The most impactful immediate lever is increasing backfill budget."

Plain:

- "The best immediate change is to let backfill run longer. Right now it stops after about 5 minutes, so I would raise that to 15 minutes."

Bad:

- "The observed throughput degradation appears to be a function of cyclical coordination between inventory-generation refresh work and bounded backfill execution, where scan overhead, scheduler phase transitions, and residual indexing-side write amplification combine to reduce end-to-end convergence velocity. The most production-ready mitigation is likely a staged combination of scheduler tuning, runtime-budget expansion, and further critical-path isolation for non-essential indexing workloads."

Plain:

- "It is slow because it still spends too much time rescanning the repo instead of backfilling PRs. The quickest fix is to let backfill run longer each time. After that, the bigger fix is to make full repo scans happen less often."

Bad:

- "The architectural direction here is to decouple canonical object identity from mutable lookup surfaces, so that rename churn, fork divergence, and alias reassignment can be handled within a more durable reconciliation model."

Plain:

- "The clean fix is to treat the permanent ID as the real identity, and treat the name as something that can change."

Bad:

- "The remaining production issue is not a fundamental systems-design failure, but rather an inconsistency in how repository identity is modeled at the persistence boundary."

Plain:

- "The main design is fine. The problem is that the database is treating the repo name as permanent when it is not."

Bad:

- "The backend remains operational, but residual synchronization drag is still observable in the form of non-critical indexing-side work, intermittent queue-control noise, and cyclical inventory refresh overhead."

Plain:

- "The system is working now, but a few smaller things are still slowing it down."
