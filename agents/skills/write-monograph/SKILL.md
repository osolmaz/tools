---
name: write-monograph
description: Use when planning, drafting, revising, or reviewing a mathematical or technical monograph, lecture-note sequence, long-form tutorial, or textbook chapter. Helps build exposition from motivation to formal definitions, propositions, proofs, examples, applications, questions, exercises, and solutions without dumping unexplained formulas or inventing facts to fit a template.
---

# Write Monograph

Use this skill to write rigorous long-form technical exposition that teaches a
subject by building it in layers.

The goal is not to make the text easy by removing rigor. The goal is to make
rigor feel inevitable: each definition, theorem, notation choice, proof, example,
algorithm, and exercise should answer a need the reader has already seen.

## Non-Negotiable Exposition Rules

No section may become a dump of formulas, theorem statements, or definitions one
after another.

Every displayed formula must be introduced by prose that says why it appears,
what problem it addresses, or what the reader should notice. After a displayed
formula, add prose that interprets it, names the important terms, explains the
transition, or states what has been gained, unless the formula is an immediate
continuation of the same short derivation.

Long derivations must be broken into stages. Between stages, explain the goal,
the invariant, the simplification, or the reason the next manipulation is valid.
The reader should be able to follow the conceptual path from the surrounding
paragraphs before checking every algebraic detail.

Use formulas as load-bearing parts of the exposition, not as a replacement for
exposition.

## Heuristic, Not A Template

The structure in this skill is a suggested teaching pattern, not a strict
formula.

Do not invent definitions, examples, applications, historical motivation,
theorems, citations, exercises, or domain facts just to satisfy this pattern. If
the source material does not support a section, write a narrower true section,
say what is missing, or ask for the needed source/context.

Truth, source fidelity, and mathematical correctness come before matching the
recommended sequence. Drop, merge, or reorder steps when the subject demands it.

## Markdown Formatting

When writing Markdown, use clean semantic headings without manual section
numbers.

Write:

```markdown
## Dennard Formulation
## KV-Aware Bounds
```

Do not write:

```markdown
## 1. Dennard Formulation
## 2. KV-Aware Bounds
```

Let the renderer, table of contents, or surrounding publication system provide
numbering when numbering is needed. Use ordered lists for actual ordered steps,
procedures, or exercise lists, not for section titles.

Only preserve manual numbering in headings when the user explicitly asks for it,
or when rewriting an existing source whose section numbers must remain stable
for citation or cross-reference.

Make headings labels, not sentences. A heading names the topic of its section as
a noun phrase — "The Capacity Limit", "Dense Transformer Adapter", "Worked
Examples" — so the reader can scan the structure. A full subject-verb-object
heading ("Capacity Caps the Batch") pre-empts the section and reads as a slogan,
the more so when several sibling headings are stamped from one parallel template.

The exception is a deliberate major statement. A heading may be a full sentence
when that sentence is a load-bearing claim the section exists to defend — a named
law, or a thesis like "Memory Power Is the Wrong Metric for Latency". Use it
rarely: in a document whose headings are otherwise noun phrases, a sentence
heading should earn its emphasis, and two of them in a row almost never do.

After drafting, read a chapter's headings as a flat list and check that they are
the same kind of thing, labels with labels, in one register.

## Reader Contract

Write for a serious learner who is willing to work but does not yet know why the
next abstraction is necessary.

Before introducing a formal object, give the reader at least one of these:

- a concrete problem that cannot be solved cleanly without it
- a familiar lower-dimensional or smaller case
- a computational inconvenience that the abstraction removes
- a theoretical gap left by the previous section
- a real application that forces the new concept to appear

Avoid definitions that arrive as isolated declarations. A definition can be
formal and compact, but the reader should know what pressure created it.

## Global Shape

Use a staged sequence from concrete to abstract to operational.

1. Start with a motivating overview.
2. Begin the first chapter from familiar examples, history, geometry, computation, or an application.
3. Distill the shared structure into definitions.
4. Develop consequences through propositions and theorems.
5. Show how the formalism acts on examples.
6. Turn recurring proof or computation patterns into practical methods.
7. Close chapters with conceptual questions, exercises, and solutions or solution sketches.
8. Let later chapters reuse previous structures instead of restarting from scratch.

For a mathematical monograph, a reliable progression is:

- concrete objects and operations
- subobjects and closure conditions
- generation, independence, coordinates, and bases
- structure-preserving maps
- representations of maps by symbolic or computational objects
- operations on those representations
- algorithms and applications

For a non-mathematical technical monograph, keep the same pattern but translate
the nouns: primitives, valid substructures, composition, canonical
representations, transformations, algorithms, case studies.

## Chapter Openings

Open each chapter with a small promise, not a table of contents.

Good chapter openings do these things:

- state the new problem or capability
- identify which earlier concept is being extended
- say why the new layer matters in theory or practice
- delay full generality until the reader has a reason to want it

When the chapter is abstract, start with a familiar special case. When the
chapter is computational, start with a real problem or a small worked instance.
When the chapter introduces a representation, explain what information the
representation preserves and what choices it depends on.

## Section Pattern

Most sections should follow this rhythm:

1. Motivation: explain the need in plain technical language.
2. Recall: bring forward only the prior facts needed now.
3. Notation: introduce symbols before they appear in dense formulas.
4. Definition: state the formal object precisely.
5. Immediate consequences: record simple but useful facts.
6. Theorem or proposition: state the reusable result.
7. Proof: prove only what has not already become obvious.
8. Example: compute or test the result in a concrete case.
9. Method: if the example exposes a repeatable process, extract it.
10. Checkpoint: ask a question, leave a small verification, or point to an exercise.

Do not force every section to contain every item. Use the rhythm to prevent
lonely definitions and unsupported examples.

## Definitions

Make definitions short, named, and operational.

Before a definition:

- explain the informal idea
- identify the ambient objects and assumptions
- make clear what problem the definition solves

Inside a definition:

- state the object first
- list required properties in a stable order
- name important special cases
- define all symbols that are local to the definition

After a definition:

- test it on a simple example
- mention an obvious non-example when it prevents a common mistake
- point out which clauses are the ones that must actually be checked

When a long axiom list is unavoidable, immediately compress it into a practical
test or criterion if one exists.

## Notation

Introduce notation just in time and attach meaning to the subscript, superscript,
index, or decoration.

Use notation to reduce cognitive load, not to advertise generality. If an object
depends on choices, say so near the notation. For example, when a representation
depends on a basis, coordinate system, convention, ordering, model, or
normalization, make that dependence explicit before simplifying the notation.

Prefer this order:

1. plain-language role
2. formal symbol
3. dependency or convention
4. simplified symbol used later

Return to the meaning of notation when it reappears after a long gap.

## Theorems And Proofs

State theorems in the form the reader can use.

Before a theorem, give one sentence explaining what it will let the reader do:
test a property, build an object, compute a value, classify cases, or connect two
views of the same structure.

Use proofs to reveal why the statement is true, not just to certify it. Good
proofs in this style often:

- recall the exact earlier criterion being applied
- prove both directions explicitly when the statement is an equivalence
- name the inclusion or implication currently being shown
- reduce a general claim to a generic element
- reuse definitions instead of invoking hidden intuition
- end by stating what has been established

It is acceptable to omit a proof when it would interrupt the main lesson, but say
why it is omitted and use the theorem immediately so the reader sees its value.
Do not omit the proof of a result that is the conceptual hinge of the chapter.

## Examples

Use examples for distinct jobs.

- First example: show the definition in the smallest nontrivial setting.
- Contrast example: show why a plausible false statement fails.
- Computation example: demonstrate a repeatable calculation.
- Choice-sensitive example: show how a result changes when a basis, convention,
  coordinate system, or parameter changes.
- Reverse example: start from the representation and recover the object.
- Application example: connect the theory to a real domain.

After each substantial example, say what the example demonstrates. If the example
contains an unfinished but useful computation, mark it as an exercise and make
sure the required technique has already appeared.

## Practical Methods

When a calculation appears more than once, extract a method box.

Write method boxes as imperative procedures. Keep them short enough to execute.

Include:

- inputs and assumptions
- the ordered steps
- the test for success or failure
- how to interpret the result
- a warning about the most common invalid case

Place method boxes after the motivating theorem and at least one example, unless
the method is the reason the theorem is being introduced.

## Applications

Use applications to justify the theory, not to decorate it.

A good application section should:

- begin with a real question
- translate domain facts into the formal language of the chapter
- solve the formal problem with the tools already built
- translate the result back into the domain
- mention constraints that come from reality rather than the formal model

Keep applications concrete. Electrical networks, chemical balancing,
cryptography, color perception, physical models, algorithms, and data examples
work because they force the abstraction to do visible work.

## Questions And Exercises

End chapters with two different kinds of practice.

Conceptual questions should test whether the reader can recall and explain the
main definitions, criteria, theorem statements, and relationships. Ask for exact
formulations, differences between similar notions, and reasons a method applies.

Exercises should make the reader use the machinery.

Include a mix of:

- definition checks
- proof completions
- small computations
- counterexamples
- construction tasks
- application problems
- reverse-engineering tasks

Order exercises from direct checks to synthesis. If solutions are included,
encourage the reader to attempt the work first, then provide enough detail to
show the method, not merely the answer.

## Sentence-Level Voice

State claims positively. Avoid the negation-contrast reframe — "it is not X, it
is Y", "not X but Y", "X isn't about Y, it's about Z", "the point isn't X, it's
Y". This antithesis construction is a recognizable marker of machine-generated
prose, and it forces the reader to hold a clause (X) that the sentence
immediately throws away. Say Y directly.

Rewrite the reframe into a plain assertion:

- "It is not a benchmark predictor. It is a roofline." becomes "It is a
  roofline."
- "The product appears not because we multiplied two specs, but because
  throughput factors into parallelism times step rate." becomes "The product
  appears because throughput factors into parallelism times step rate."
- "This is a batched-throughput statement, not a latency statement." becomes
  "This governs batched throughput." — then show the degenerate case directly.

A plain negation is fine when the negation is the content: a genuine
non-equivalence ("fitting in memory does not imply serving usefully"), a
disambiguation between two real quantities, or a warning about a real
misconception. Use it once, plainly, without the paired "it is Y" reveal that
turns the fact into a rhetorical move.

## Revision Checklist

Before considering a chapter ready, check:

- The chapter says what new capability it gives the reader.
- No section degenerates into formulas or formal statements without explanatory
  paragraphs between them.
- Every major definition is motivated before it is stated.
- Displayed formulas are introduced and interpreted in prose.
- Notation is introduced before dense use and dependencies are named.
- Theorems are followed by proofs, examples, or a clear reason for omission.
- Examples are not all of the same type.
- At least one recurring computation has been converted into a practical method.
- Applications are solved by the chapter's tools, not pasted in as anecdotes.
- Questions test concepts; exercises test use.
- Later sections refer back to earlier results by name or role.
- The text does not overgeneralize before the reader has seen the small case.
- The suggested structure has not forced unsupported or fabricated facts.
- Markdown headings do not contain manual numbers unless they are explicitly
  required for stable references.
- No sentence uses the "it is not X, it is Y" antithesis reframe where a direct
  positive statement would serve.
- Headings are noun-phrase labels in a consistent register, except where a full
  sentence is a deliberate major statement.

## Avoid

- Dumping formulas, equations, definitions, or theorem statements one after
  another without explanatory prose.
- Making up motivation, examples, applications, or facts to satisfy the skill's
  suggested structure.
- Numbering Markdown headings by hand when plain semantic headings would work.
- Starting with a maximally general definition when a familiar case can motivate it.
- Introducing notation only inside a formula and explaining it later.
- Treating examples as optional after a hard theorem.
- Hiding choice-dependence in representations.
- Giving applications that do not use the theory.
- Writing exercises that only repeat the worked examples with new numbers.
- Collapsing proof, computation, and explanation into one unstructured block.
- Making the monograph sound like a survey when it is meant to teach.
- Writing headings as full sentences or slogans ("Capacity Caps the Batch") when
  a noun-phrase label would serve, or stamping sibling headings from one parallel
  template. Reserve sentence headings for deliberate major statements.
- Using the negation-contrast reframe ("it is not X, it is Y"; "not X but Y";
  "X isn't about Y, it's about Z"). State Y directly; the reframe reads as
  machine-generated and makes the reader hold a clause that is immediately
  discarded.
