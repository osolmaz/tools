# Data Model Review Tool Implementation Plan

## Objective

Build a problem-agnostic data model reviewer and simplifier that converges on a
minimum viable schema. The tool should extract proposed data models into a
normalized field graph, run independent reviews for every added or changed
field/column, aggregate simplification decisions, apply safe changes, and repeat
until no reviewer can simplify the model further.

The skill remains the agent-facing workflow. The tool becomes the deterministic
execution and validation layer behind that workflow.

## Core Principle

Do not rely on an agent to remember every nested field.

The extractor must enumerate the model graph. Every field, nested field, column,
selector key, policy key, JSON Schema property, SQL column, and object-like
subfield must become an explicit review item or an explicit opaque exemption.

Markdown is a report format, not the source of truth.

## Architecture

### 1. Extract

Parse source schemas and produce a normalized JSON field graph.

Supported sources, in priority order:

1. JSON Schema files.
2. Markdown fenced JSON Schema, TypeScript, YAML, and SQL blocks.
3. TypeScript type aliases and interfaces.
4. SQL `CREATE TABLE` statements.
5. YAML/KRM resources.
6. OpenAPI schemas and `$ref` graphs.

Use real parsers where available:

- TypeScript: TypeScript compiler API or `ts-morph`.
- JSON/JSON Schema: native JSON parser plus `$ref` resolution.
- YAML/KRM: YAML parser plus JSON Pointer traversal.
- SQL: dialect-aware parser such as `sqlglot`, with dialect selection.
- OpenAPI: OpenAPI parser plus component schema traversal.

Initial MVP may support fewer extractors, but the field graph contract should
not change when new extractors are added.

### 2. Normalize

Convert extracted models into a language-agnostic graph.

```json
{
  "schemaVersion": 1,
  "source": {
    "path": "rfcs/0009-model-harness-profiles.md",
    "revision": "git-sha-or-null"
  },
  "models": [
    {
      "id": "ModelProfilePolicy",
      "kind": "object",
      "source": {
        "path": "rfcs/0009-model-harness-profiles.md",
        "span": {
          "startLine": 380,
          "endLine": 395
        }
      },
      "fields": [
        {
          "path": "promptRecipe",
          "name": "promptRecipe",
          "type": "\"standard-v1\" | \"gpt-5-v1\"",
          "required": false,
          "nullable": false,
          "parent": "ModelProfilePolicy",
          "objectLike": false,
          "source": {
            "path": "rfcs/0009-model-harness-profiles.md",
            "span": {
              "startLine": 390,
              "endLine": 390
            }
          }
        }
      ]
    }
  ]
}
```

Required graph concepts:

- `model.id`
- `model.kind`
- `field.path`
- `field.name`
- `field.type`
- `field.required`
- `field.objectLike`
- `field.source`
- parent/child relationships
- references to named models, tables, or schemas

### 3. Review

Spawn one independent review run per added or changed field/column.

Each sub-run receives:

- model purpose;
- current required use cases;
- the full current schema for context;
- the normalized field graph;
- exactly one field or column under review;
- naming conventions and minimum viable schema rules.

Each sub-run must return structured JSON:

```json
{
  "schemaVersion": 1,
  "model": "ModelProfilePolicy",
  "fieldPath": "promptRecipe",
  "decision": "rename",
  "finalName": "systemPromptVariant",
  "finalType": "\"standard-v1\" | \"gpt-5-v1\"",
  "required": false,
  "rationale": "The field is needed only as a code-owned prompt contribution selector. Recipe is too broad.",
  "alternatives": [
    "systemPromptVariant",
    "promptContributionSet",
    "remove"
  ],
  "simplestChoice": "systemPromptVariant",
  "confidence": "medium",
  "questions": []
}
```

Allowed decisions:

- `keep`
- `rename`
- `merge`
- `derive`
- `move`
- `defer`
- `remove`
- `opaque`

`opaque` is allowed only for fields that intentionally remain uninterpreted by
the current layer, and it requires a justification plus an owner boundary.

### 4. Aggregate

The coordinator reads all field review JSON files and produces an aggregate
decision file.

The aggregator must:

- fail if any extracted field lacks a review;
- fail if any object-like field lacks nested reviews or an `opaque` exemption;
- group overlapping rename/merge/remove recommendations;
- identify conflicts between reviewers;
- require a conflict-resolution run when decisions cannot be applied together;
- reject new fields introduced by the coordinator unless they get their own
  field review.

### 5. Apply

The reducer applies safe simplifications as a patch.

Default policy:

- Apply high-confidence `remove` when the field lacks a current use case.
- Apply `rename` when it improves clarity and matches local naming conventions.
- Apply `merge` only when the target field is reviewed and can cover both use
  cases.
- Apply `derive` by removing stored data only when derivation is deterministic
  and the source fields remain available.
- Apply `defer` by removing the field and recording the deferred requirement.
- Do not apply low-confidence or conflicting recommendations without a focused
  conflict review.

### 6. Iterate

After applying changes:

1. Re-extract the graph.
2. Compare it with the previous graph.
3. Spawn reviews for all new, changed, or still-questionable fields.
4. Aggregate and apply again.
5. Repeat until stable.

Convergence means:

- no reviewer recommends `remove`, `rename`, `merge`, `derive`, `move`, or
  `defer`;
- no object-like field has unreviewed nested fields;
- no final field lacks a review decision;
- no removed/deferred field remains in the final schema;
- no new field was introduced without review;
- the final schema still satisfies declared required use cases.

### 7. Report

Generate Markdown from the JSON artifacts.

The report should include:

- model purpose;
- required use cases;
- iteration count;
- field graph summary;
- per-field decisions;
- fields removed;
- fields renamed;
- fields merged;
- fields derived instead of stored;
- fields deferred;
- opaque fields and owner boundaries;
- final schema;
- convergence status.

## File Layout

Recommended output directory:

```text
.data-model-review/
  requirements.md
  graph.iteration-1.json
  reviews.iteration-1/
    ModelProfilePolicy.promptRecipe.review.json
    ModelProfilePolicy.reasoningDefault.review.json
  aggregate.iteration-1.json
  patch.iteration-1.diff
  graph.iteration-2.json
  reviews.iteration-2/
  aggregate.iteration-2.json
  final-report.md
```

Review files should be validated by JSON Schema:

```text
agents/skills/data-model/schemas/model-graph.schema.json
agents/skills/data-model/schemas/field-review.schema.json
agents/skills/data-model/schemas/aggregate-review.schema.json
```

## CLI Shape

Target command family:

```bash
data-model-review extract --source schema.ts --out .data-model-review/graph.iteration-1.json
data-model-review review --graph .data-model-review/graph.iteration-1.json --out .data-model-review/reviews.iteration-1
data-model-review aggregate --graph .data-model-review/graph.iteration-1.json --reviews .data-model-review/reviews.iteration-1 --out .data-model-review/aggregate.iteration-1.json
data-model-review apply --source schema.ts --aggregate .data-model-review/aggregate.iteration-1.json --out .data-model-review/patch.iteration-1.diff
data-model-review validate --graph .data-model-review/graph.iteration-2.json --reviews .data-model-review/reviews.iteration-2
data-model-review report --run .data-model-review --out .data-model-review/final-report.md
```

Eventually add:

```bash
data-model-review run --source schema.ts --requirements requirements.md --out .data-model-review
```

## Agent Integration

The `data-model` skill should eventually instruct agents to use this tool before
finalizing a schema.

Required agent behavior:

1. Extract the graph.
2. Run independent per-field reviews.
3. Aggregate decisions.
4. Apply safe simplifications.
5. Repeat until convergence.
6. Generate Markdown report.
7. Update final schema only after validation passes.

Agents must not finalize while validation reports missing reviews, unreviewed
nested fields, unresolved simplification recommendations, or schema/report
drift.

## Open Design Questions

- Which extractor should ship first: JSON Schema, TypeScript, or SQL?
- Should review sub-runs be spawned through Codex sessions, local worker agents,
  GitHub PR comments, or a generic command adapter?
- Should low-confidence keep/remove decisions trigger automatic second opinions?
- How should requirements be represented so the reducer can verify the final
  schema still satisfies them?
- How much of the apply step should be automated versus patch-proposed for
  human/agent review?
