---
description: Prompt for taking one implementation plan, executing it end-to-end on the current branch or PR, testing it, running Codex review, checking CI/CD, and reporting the result without auto-merging
---

This prompt must process exactly one implementation plan per run. Do not batch multiple plans, and do not switch to a different plan mid-run.

1. Take exactly one implementation plan as input. Read it fully before you start coding. Treat the plan as the source of truth for the intended work unless the repo state proves it is outdated or underspecified.

2. Implement the plan end-to-end. If context compaction happens, re-read the plan and the current branch or PR state before continuing so you do not drift away from the intended path. Finish the actual implementation rather than stopping at analysis.

3. If there is already a PR open for this implementation plan, keep working in that same PR. If there is no PR yet, open one once the implementation is ready to share.

4. If the repo state and the plan disagree in a meaningful way, stop and resolve that mismatch explicitly instead of improvising around it. Do not quietly drift away from the plan just because the context got compressed or the work became inconvenient.

5. Once implementation is complete, test it. Choose the most direct validation for the change: targeted tests, local smoke tests, dev servers, real requests, or other practical checks. Test as much as possible without merging. State explicitly what could not be tested locally and what still needs staging or production verification.

6. Push your latest commits before running review so the review is always against the current PR head.

7. Run Codex review against the correct base branch: `codex review --base <branch_name>`. Use a 30 minute timeout on the tool call available to the model, not the shell `timeout` program.

8. Run Codex review in a loop and address any P0 or P1 issues that come up until there are none left. Ignore issues related only to supporting legacy or cutover unless the plan for this work explicitly includes that scope. Lower-severity findings can be handled with judgment, but unresolved P0 or P1 findings block the PR.

9. Check both inline review comments and PR issue comments dropped by Codex on the PR, and address them if they are valid. Ignore them if they are irrelevant. Ignore stale comments from before the latest commit unless they still apply. In either case, make sure the comments are replied to and resolved. If your last commit was recent, wait 5 minutes for late review comments to arrive before concluding the PR is clear.

10. Check CI/CD for the PR. If everything is green, that part is satisfied. If something is failing, determine whether it is actually caused by your changes. If failures are unrelated, pre-existing, or due to external churn outside the diff, state that explicitly and do not treat them as blockers. If failures are plausibly related to the PR, fix them before declaring the PR ready.

11. Once CI/CD is green and you think the PR is ready to merge, post a final report on the PR itself. Include a plain-language summary of what changed, the exact validation commands you ran and their outcomes, any remaining non-blocking caveats, and whether the PR is ready for human review or landing.

12. Finish by giving the same summary and PR link back to the operator. Do not merge automatically unless the user explicitly asks.
