---
name: autodoc
description: Use when preparing or updating an implementation plan, documentation, or specification before implementation, including choosing the right repository and applying SimpleDoc conventions.
---

# Autodoc

- Prepare the plan and documentation.
- Create or update the plan for the most elegant and long-term production-ready solution, but do not take longer than necessary.
- Preserve the entropy and information in the user's request, including its intent, when writing the plan. Keep the user's concern and any specific wording that carries important meaning near the start of the document, in an introduction that clearly states its intended purpose or goal.
- If there is no plan markdown document for the task which the skill is triggered for, create a `.md` file for that plan and then proceed with implementation.
- If the repo is owned by `osolmaz`, create or update the documentation, specification, and implementation plan in the relevant repo or repos, depending on the context.
- If it is someone else's project, create them in the scratch repo at `~/scratch`. Keep the plan outside someone else's implementation repo unless the user explicitly asks to track it there.
- Create or update the requisite amount of documentation in either existing files or new files in the relevant repos.
- Avoid unnecessary duplication and keep the relevant existing documentation up to date.
- Do not spend a long time updating a large set of docs only for this purpose.
- Use the `simpledoc` skill and follow the SimpleDoc convention when creating or updating documentation.
- Use capitalized filenames for evergreen, long-term documentation and specifications, and dated SimpleDoc filenames for time-bound documents tied to a certain time.
- Name specification files after the feature itself without `spec` or `specification` in the filename. The document title may include `Spec` or `Specification`.
- End filenames for non-evergreen implementation plans with `-plan.md`, not `-implementation-plan.md`.
- Use `cutover` only to describe replacement behavior in prose. Do not use `cutover` or `cutover plan` in filenames, document titles, headings, plan names, issue titles, pull request titles, commit subjects, test names, or other identifiers. Name the target capability directly, adding `plan` only when a plan suffix is useful.
- Use the `kill-ai-smell` skill for capitalized evergreen documents. AI smell may remain in one-off implementation plans.
- Use `[skip ci]` in the commit message for documentation-only changes.
- Run `npx -y @simpledoc/simpledoc check` (or `simpledoc check`) locally in each repo where documentation changed.
