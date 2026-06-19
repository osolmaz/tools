---
name: data-model
description: Use when creating or revising data models, JSON files, JSON schemas, API payload schemas, database schemas, SQL tables, migrations, or any structured set of keys/fields/columns. Forces a minimum viable schema review with an information table for every proposed field or SQL column, a separate reasoning step, a separate decision table, and a final revised model.
---

# Data Model

Use this skill whenever you create a first version of a data model, JSON shape,
JSON Schema, API payload schema, SQL table, database migration, event payload,
or other structured model made of named fields or columns.

The goal is a minimum viable schema: the smallest set of keys or columns that
preserves the required behavior, is clear to future readers, and avoids
premature modeling.

Use Schemator's Lindy and simplicity criteria as the standard for judging the
model. See `dutifuldev/schemator` or the `$schemator` skill for the fuller
workflow: prefer the smallest durable schema, boring names, clear current use
cases, fewer fields, derived values over stored values when safe, and no
future-proof fields whose only reason is "might need later."

## Required Workflow

Do these steps in order. Do not skip the information or decision table because
the first schema looks obvious.

1. State the model's purpose in one or two sentences.
2. List the concrete use cases the model must support now.
3. Draft the smallest plausible first schema.
4. Create a separate Markdown review file for each data model or SQL table.
5. In that review file, fill an information table for every proposed field or
   SQL column. Do not include decisions in this table.
6. In that review file, reason over the table in prose, looking for redundant
   fields, unclear names, missing current use cases, derived values, and
   premature future-proofing.
7. In that review file, fill a separate decision table for every proposed field
   or SQL column.
8. In that review file, add a final reflection that explains what changed from
   the first draft and what was intentionally left out.
9. Prune or rename fields based on the decision table.
10. Produce the revised final schema.

## Review File

Do the field-by-field reasoning work in Markdown, not only in chat. Create one
review file per data model or SQL table. If the repo has a docs or design-notes
convention, follow it. Otherwise use a local path such as:

```text
docs/data-models/<model-name>.md
```

For temporary or exploratory work that should not be committed, ask where the
review file should live or place it in an existing scratch/planning area. Do not
mix multiple unrelated models into one review file.

Each review file must contain:

1. Purpose.
2. Current use cases.
3. First draft schema.
4. Information table.
5. Reasoning step.
6. Decision table.
7. Final revised schema.
8. Final reflection.

When editing files, update the actual JSON Schema, migration, SQL table, or
model implementation only after the review file reaches the final revised
schema.

## Information Table

Create one Markdown table per model/table. For a SQL table, each row is one
column. For JSON or JSON Schema, each row is one key/property. This table is
only for facts and options. Do not decide whether to keep or remove fields here.

Use this exact table shape unless the user asks for a different format:

| Field/column | Type | Required? | Purpose | Why might it belong? | Alternatives / synonyms | Simplest option |
| --- | --- | --- | --- | --- | --- | --- |
| `name` | `string` | yes | Human-readable label | Required for display and search | `title`, `label`, `displayName` | `name` is shortest and common |

Column meanings:

- `Field/column`: exact proposed key or SQL column name.
- `Type`: JSON type, JSON Schema type, SQL type, enum, reference, or nested
  object summary.
- `Required?`: `yes`, `no`, or the specific condition.
- `Purpose`: what behavior or query needs this data.
- `Why might it belong?`: the strongest argument that the field could belong in
  version one.
- `Alternatives / synonyms`: other names, encodings, normalized forms, or places
  this data could live.
- `Simplest option`: the option chosen after considering alternatives.

## Reasoning Step

After the information table, write a short reasoning pass before making
decisions. Address:

- fields that overlap or duplicate each other;
- names that have simpler or more conventional alternatives;
- fields that can be derived instead of stored;
- fields that lack a current required use case;
- fields that are too broad, such as `metadata`, `extra`, `payload`, or
  `config`;
- fields that should be deferred because they are only future-proofing.

## Decision Table

After the reasoning step, create a separate Markdown decision table for every
field or SQL column from the first draft.

Use this exact table shape unless the user asks for a different format:

| Field/column | Decision | Final name | Final type | Required? | Reason |
| --- | --- | --- | --- | --- | --- |
| `name` | keep | `name` | `string` | yes | Short conventional name required for display and search |

Allowed decisions:

- `keep`
- `rename`
- `merge`
- `derive instead`
- `move`
- `defer`
- `remove`

If a proposed field has no clear current use case, mark it `remove` or `defer`,
then remove it from the final schema.

## Minimum Viable Schema Rules

- Prefer fewer fields until a real use case requires more.
- Prefer stable, conventional names over clever or domain-internal names.
- Prefer one field with clear semantics over multiple partially overlapping
  fields.
- Prefer derived values over stored values unless storing avoids real
  correctness, performance, or audit problems.
- Prefer normalized references only when the model needs joins, independent
  lifecycle, or deduplication now.
- Avoid vague fields such as `metadata`, `extra`, `data`, `payload`, `options`,
  or `config` unless the schema explicitly needs an extension point.
- Avoid parallel synonyms such as both `name` and `title`, or both `status` and
  `state`, unless their meanings are distinct and documented.
- Avoid future-proof fields whose only rationale is "might need later."
- For timestamps, choose the minimum necessary lifecycle fields, usually
  `created_at`/`updated_at` in SQL or `createdAt`/`updatedAt` in JSON.
- For enums, start with known states only and document how unknown future states
  should be handled.

## Naming Defaults

Use the surrounding codebase's naming style. If there is no local convention:

- JSON/API fields: `camelCase`.
- SQL columns: `snake_case`.
- Boolean fields: name them as predicates, such as `isActive`, `hasAccess`, or
  `archived`.
- Foreign keys: use `<entity>_id` in SQL and `<entity>Id` in JSON.
- Timestamps: use `<event>_at` in SQL and `<event>At` in JSON.

## Final Output

After the decision table, rewrite the proposal in the review file. The final
answer should include:

1. The review file path for each data model.
2. The revised schema or SQL table.
3. A short reflection:
   - fields removed or merged;
   - fields renamed and why;
   - fields intentionally deferred;
   - remaining assumptions or open questions.

If editing files, update the actual schema/migration/model after the reflection
and make sure the final implementation matches the revised proposal, not the
first draft.
