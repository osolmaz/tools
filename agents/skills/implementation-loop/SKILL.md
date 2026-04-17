---
name: implementation-loop
description: Use when the user asks to implement a plan end-to-end, test it, run codex review against the base branch in a loop until no P0/P1 issues remain, and make sure CI/CD is green before finishing.
---

Do the following in the given order

1. Implement the given plan end-to-end. If there is no plan markdown document for the task which the skill is triggered for, create a `.md` file in `~/scratch-repo` for that plan and then proceed with implementation. If context compaction happens, make sure to re-read the plan to stay on track. Finish to completion. If there is a PR open for the implementation plan, do it in the same PR. If there is no PR already, open PR.

2. Once you finish implementing, make sure to test it. This will depend on the nature of the problem. If needed, run local smoke tests, spin up dev servers, make requests and such. Try to test as much as possible, without merging. State explicitly what could not be tested locally and what still needs staging or production verification.

3. Push your latest commits before running review so the review is always against the current PR head. Run codex review against the base branch: `codex review --base <branch_name>`. Use a 30 minute timeout on the tool call available to the model, not the shell `timeout` program. Do this in a loop and address any P0 or P1 issues that come up until there are none left. Ignore issues related to supporting legacy/cutover, unless the plan says so. We do cutover most of the time.

4. Check both inline review comments and PR issue comments dropped by Codex on the PR, and address them if they are valid. Ignore them if irrelevant. Ignore stale comments from before the latest commit unless they still apply. Either case, make sure that the comments are replied to and resolved. Make sure to wait 5 minutes if your last commit was recent, because it takes some time for review comment to come.

5. In the final step, make sure that CI/CD is green. Ignore the fails unrelated to your changes, others break stuff sometimes and don't fix it. Make sure whatever changes you did don't break anything. If CI/CD is not fully green, state explicitly which failures are unrelated and why.

6. Once CI/CD is green and you think that the PR is ready to merge, finish and give a summary with the PR link. Include the exact validation commands you ran and their outcomes. Also comment a final report on the PR.

7. Do not merge automatically unless the user explicitly asks.
