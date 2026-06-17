---
name: data-model
description: Use when creating or revising data models, JSON files, JSON schemas, API payload schemas, database schemas, SQL tables, migrations, or any structured set of keys/fields/columns. Forces a minimum viable schema review with a Markdown table for every proposed field or SQL column, including rationale, alternatives, synonyms, pruning decisions, and a final revised model.
---

# Data Model

Use this skill whenever you create a first version of a data model, JSON shape,
JSON Schema, API payload schema, SQL table, database migration, event payload,
or other structured model made of named fields or columns.

The goal is a minimum viable schema: the smallest set of keys or columns that
preserves the required behavior, is clear to future readers, and avoids
premature modeling.

## Required Workflow

Do these steps in order. Do not skip the reflection table because the first
schema looks obvious.

1. State the model's purpose in one or two sentences.
2. List the concrete use cases the model must support now.
3. Draft the smallest plausible first schema.
4. Fill a Markdown scrutiny table for every proposed field or SQL column.
5. Prune or rename fields based on the table.
6. Produce the revised final schema.
7. Add a final reflection that explains what changed from the first draft and
   what was intentionally left out.

## Scrutiny Table

Create one Markdown table per model/table. For a SQL table, each row is one
column. For JSON or JSON Schema, each row is one key/property.

Use this exact table shape unless the user asks for a different format:

| Field/column | Type | Required? | Purpose | Why keep it? | Alternatives / synonyms | Simplest choice | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `name` | `string` | yes | Human-readable label | Required for display and search | `title`, `label`, `displayName` | `name` is shortest and common | keep |

Column meanings:

- `Field/column`: exact proposed key or SQL column name.
- `Type`: JSON type, JSON Schema type, SQL type, enum, reference, or nested
  object summary.
- `Required?`: `yes`, `no`, or the specific condition.
- `Purpose`: what behavior or query needs this data.
- `Why keep it?`: the strongest argument that the field belongs in version one.
- `Alternatives / synonyms`: other names, encodings, normalized forms, or places
  this data could live.
- `Simplest choice`: the option chosen after considering alternatives.
- `Decision`: `keep`, `rename to ...`, `merge with ...`, `derive instead`,
  `move to ...`, or `remove`.

If a proposed field has no clear current use case, mark it `remove` or
`defer`, then remove it from the final schema.

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

After the table, rewrite the proposal. The final answer should include:

1. The revised schema or SQL table.
2. The scrutiny table.
3. A short reflection:
   - fields removed or merged;
   - fields renamed and why;
   - fields intentionally deferred;
   - remaining assumptions or open questions.

If editing files, update the actual schema/migration/model after the reflection
and make sure the final file matches the revised proposal, not the first draft.
