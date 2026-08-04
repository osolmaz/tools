---
name: autoimplement
description: Use when the user asks to implement a plan end-to-end, test it, run Pi Reviewer against the base branch in a loop until no P0/P1 issues remain, and make sure CI/CD is green before finishing.
---

Do the following in the order that makes sense. Choose the most efficient order for dependencies, and parallelize independent work.

0. Prepare the plan and documentation.
   - Create or update the plan for the most elegant and long-term production-ready solution, but do not take longer than necessary.
   - If there is no plan markdown document for the task which the skill is triggered for, create a `.md` file for that plan and then proceed with implementation.
   - If the repo is owned by `osolmaz`, create or update the documentation, specification, and implementation plan in the relevant repo or repos, depending on the context.
   - If it is someone else's project, create them in the scratch repo at `~/scratch`. Keep the plan outside someone else's implementation repo unless the user explicitly asks to track it there.
   - Follow the SimpleDoc convention when creating or updating documentation:
     - Use capitalized filenames for evergreen, long-term documentation and specifications, and dated SimpleDoc filenames for time-bound documents tied to a certain time.
     - Use the `kill-ai-smell` skill for capitalized evergreen documents. AI smell may remain in one-off implementation plans.
     - Run `npx -y @simpledoc/simpledoc check` (or `simpledoc check`) locally in each repo where documentation changed.

1. Implement the given plan end-to-end.
   - Implement the most elegant and long-term production-ready solution, but do not take longer than necessary.
   - Context compaction might happen during implementation or review. If not enough of the plan was preserved after compaction, re-read the written plan to stay on track with the plan.
   - Finish to completion. If there is a PR open for the implementation plan, do it in the same PR. If there is no PR already, open PR.
   - Before finishing, commit and push any new or changed documentation, specification, or plan file in the relevant repo or repos, including the `~/scratch` repo when used, unless the user asked not to.

2. Once you finish implementing, make sure to test it.
   - This will depend on the nature of the problem. If needed, run local smoke tests, spin up dev servers, make requests and such.
   - Try to test as much as possible, without merging.
   - State explicitly what could not be tested locally and what still needs staging or production verification.
   - Do not put mutation testing on the critical path unless repository policy explicitly requires it; keep the mutation test scripts available.

3. Push your latest commits before running review so the review is always against the current PR head.
   - Run Pi Reviewer with GPT-5.6 Terra at high thinking against the base branch: `pi-reviewer --model openai-codex/gpt-5.6-terra --thinking high --base <branch_name>`.
   - Use a 10 minute timeout on the tool call available to the model, not the shell `timeout` program. If Pi Reviewer takes more than 10 minutes, kill it.
   - Do not silently fall back to `codex review` when Pi Reviewer is unavailable; stop and report the missing command or configuration.
   - Run Pi Reviewer in a loop and address any P0 or P1 issues until there are none left. If a run reports only P2 or lower issues, move to the next stage.
   - Ignore issues about supporting legacy behavior unless the plan requires compatibility.
   - Look at CI only after Pi Reviewer passes, meaning the last completed run found no issues or only P2 or lower issues.

4. Pi Reviewer reports findings locally and does not post them to the pull request.
   - Separately check existing inline review comments and PR issue comments, and address valid comments.
   - Ignore irrelevant comments and stale comments from before the latest commit unless they still apply.
   - Reply to and resolve each comment either way.
   - Do not wait a fixed five minutes; wait only when a required review is known to be pending, and keep that wait bounded.

5. In the final step, make sure that CI/CD is green.
   - Ignore the fails unrelated to your changes, others break stuff sometimes and don't fix it.
   - Make sure whatever changes you did don't break anything.
   - If CI/CD is not fully green, state explicitly which failures are unrelated and why.
   - For documentation-only changes, including SimpleDoc changes, relevant local checks are enough; do not wait for CI/CD after they pass.

6. Once CI/CD is green, or the relevant local checks have passed for a documentation-only change, and you think that the PR is ready to merge, merge opportunistically unless the user explicitly asked you not to merge.
   - Then finish and give a summary with the PR link.
   - Include the exact validation commands you ran and their outcomes.
   - Also comment a final report on the PR.

7. Merge automatically unless the user explicitly asks you not to.

If this skill is queued many times, treat that as a reminder to make sure the work is fully finished. Once the work is fully finished, you can ignore the repeated instructions. If the work is not finished, continue working.
