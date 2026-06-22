---
name: data-model
description: Use when creating or revising data models, JSON files, JSON schemas, API payload schemas, database schemas, SQL tables, migrations, or any structured set of keys, fields, or columns. Acts as a lightweight wrapper around Schemator and its bundled schemator skill.
---

# Data Model

Use this skill as a pointer to Schemator, not as a separate data-model review
method. Schemator is the source of truth for reviewing schemas, simplifying
fields, checking naming, and producing auditable reports.

## How To Use It

1. Use the Schemator repository and its bundled `schemator` skill for the actual
   workflow. If the skill is installed, invoke `$schemator`; otherwise read the
   `skills/schemator/SKILL.md` file from `dutifuldev/schemator`.
2. Start from a real draft schema or proposal. If no draft exists yet, make the
   smallest useful draft first, then hand it to Schemator.
3. Provide project/task context before review so Schemator can judge names,
   field purpose, constraints, and borrowed vocabulary in context.
4. Run Schemator for extraction, review, simplification, convergence, diffing,
   or reporting as appropriate for the task.
5. Treat Schemator output as a candidate result and do the final human/product
   pass required by the `schemator` skill.

## Local Reference

The Schemator repo is expected at:

```text
~/repos/schemator
```

Typical local commands from that repo:

```bash
npm install
npm run dev -- run --source schema.md --context project-context.md --out .schemator
npm run dev -- report --run .schemator --out .schemator/final-report.md
```

Do not duplicate Schemator's review rules, report checklist, prompt guidance, or
schema criteria in this skill. Update Schemator and its bundled skills instead.
