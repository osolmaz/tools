---
name: autoimplement
description: Use when the user asks to implement a plan end-to-end, test it, run codex review against the base branch in a loop until no P0/P1 issues remain, and make sure CI/CD is green before finishing.
---

Do the following in the order that makes sense. Choose the most efficient order for dependencies, and parallelize independent work.

1. Implement the given plan end-to-end. Implement the most elegant and long-term production-ready solution, but do not take longer than necessary. If there is no plan markdown document for the task which the skill is triggered for, create a `.md` file for that plan in the scratch repo at `~/scratch` and then proceed with implementation. Keep the plan outside the implementation repo unless the user explicitly asks to track it there. If context compaction happens, make sure to re-read the plan to stay on track. Finish to completion. If there is a PR open for the implementation plan, do it in the same PR. If there is no PR already, open PR. Before finishing, commit and push any new or changed plan file in the `~/scratch` repo unless the user asked not to.

2. Once you finish implementing, make sure to test it. This will depend on the nature of the problem. If needed, run local smoke tests, spin up dev servers, make requests and such. Try to test as much as possible, without merging. State explicitly what could not be tested locally and what still needs staging or production verification. Do not put mutation testing on the critical path unless repository policy explicitly requires it; keep the mutation test scripts available.

3. Push your latest commits before running review so the review is always against the current PR head. Run Codex review with GPT-5.6 Terra at high reasoning against the base branch: `codex review -c 'model="gpt-5.6-terra"' -c 'model_reasoning_effort="high"' --base <branch_name>`. Use a 10 minute timeout on the tool call available to the model, not the shell `timeout` program. If Codex review takes more than 10 minutes, kill it. Do this in a loop and address any P0 or P1 issues that come up until there are none left. If only P2 or lesser issues are surfaced in a review run, move onto the next stage. Ignore issues related to supporting legacy/cutover, unless the plan says so. We do cutover most of the time. Look at CI only after Codex review has given a green pass, meaning the last completed turn revealed no findings or only P2 or lower.

4. Check both inline review comments and PR issue comments dropped by Codex on the PR, and address them if they are valid. Ignore them if irrelevant. Ignore stale comments from before the latest commit unless they still apply. Either case, make sure that the comments are replied to and resolved. Do not wait a fixed five minutes; wait only if a required review is known to be pending, and keep that wait bounded.

5. In the final step, make sure that CI/CD is green. Ignore the fails unrelated to your changes, others break stuff sometimes and don't fix it. Make sure whatever changes you did don't break anything. If CI/CD is not fully green, state explicitly which failures are unrelated and why.

6. Once CI/CD is green and you think that the PR is ready to merge, merge opportunistically if the user explicitly asked for autonomous merging. Then finish and give a summary with the PR link. Include the exact validation commands you ran and their outcomes. Also comment a final report on the PR.

7. Do not merge automatically unless the user explicitly asks.

If this skill is queued many times, treat that as a reminder to make sure the work is fully finished. Once the work is fully finished, you can ignore the repeated instructions. If the work is not finished, continue working.
