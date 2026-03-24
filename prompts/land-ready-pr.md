---
description: Prompt for taking one PR that is already approved for autonomous handling, completing the remaining implementation and superficial refactors, running review and CI checks, and preparing it to land without auto-merging
---

This prompt must process exactly one PR per run. Do not batch multiple PRs here, and do not switch to a different PR mid-run.

1. Take exactly one PR as input. Only use this prompt if the PR has already been triaged and deemed safe to continue autonomously. If the PR still needs human attention, stop and say so rather than continuing.

2. Finish the remaining implementation on that PR end-to-end. If context compaction happens, re-read the plan, issue, PR description, and latest branch state so you stay on track. Complete the actual work rather than stopping at analysis.

3. If the PR needs no refactor or only a superficial refactor, do that work autonomously. If you discover that the PR actually needs a fundamental refactor, stop the landing flow and route it back to the human-attention lane instead of pushing forward blindly.

4. Once implementation is complete, test it. Choose the most direct validation for the change: targeted tests, local smoke tests, dev servers, real requests, or other practical checks. Test as much as possible without merging. State explicitly what could not be tested locally and what still needs staging or production verification.

5. Push your latest commits before running AI review so the review is always against the current PR head. Run Codex review against the correct base branch: `codex review --base <branch_name>`. Use a 30 minute timeout on the tool call available to the model, not the shell `timeout` program.

6. Run the AI review in a loop and address any P0 or P1 issues that come up until there are none left. Ignore issues related only to legacy support or cutover unless the plan for this PR explicitly includes that work. Lower-severity findings can be handled with judgment, but unresolved P0 or P1 findings block the PR.

7. Check both inline review comments and PR issue comments dropped by Codex or other AI review on the PR, and address them if they are valid. Ignore them if irrelevant. Ignore stale comments from before the latest commit unless they still apply. In either case, make sure the comments are replied to and resolved. If your last commit was recent, wait long enough for late review comments to arrive before concluding the PR is clear.

8. Check CI/CD for this PR. If everything is green, that part is satisfied. If something is failing, determine whether it is actually caused by the PR. If failures are unrelated, pre-existing, or due to external churn outside the diff, state that explicitly and do not treat them as blockers. If failures are plausibly related to the PR, fix them before declaring the PR ready.

9. Once the PR is in good shape, post a final report on the PR itself. Include the plain-language summary of what changed, the exact validation commands you ran and their outcomes, any remaining non-blocking caveats, and whether the PR is ready to land.

10. Finish by giving the same summary and PR link back to the operator. Do not merge automatically unless the user explicitly asks.
