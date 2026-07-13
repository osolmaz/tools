---
name: kill-ai-smell
description: Remove AI writing tells from prose, headings, openings, and page structure. Use when writing or editing anything meant to read as human-written, including blog posts, site copy, documentation, README text, reports, PR descriptions, and emails. Trigger when the user mentions AI smell, AI tells, slop, em dashes, or prose sounding AI-written.
---

# Kill AI smell

AI-written text has recognizable tells, and readers who spot them discount
the whole document. The tells run deeper than word choice. They show up in
punctuation, in sentence shape, in how a document opens, in what headings
look like, and in the layout of a page. This skill covers each level in
turn, from the smallest unit to the whole document. Apply the rules to
everything you write or edit, and sweep for violations before finishing
any writing task.

One principle governs all of it: write for a reader who is following a
thought from beginning to end. Slop mentions things; writing explains
them. When a passage lists facts without saying why the reader should
care, or compresses context into fragments the reader must decode, the
fix is to rewrite it as sentences that carry the reader forward. Every
rule below is a special case of this.

Knowing these rules is no defense against violating them. The patterns
are how models write by default, so they appear even in text about the
patterns. Sweep your own output mechanically; do not trust your ear.

## Punctuation

**Em dashes.** At most one set per 1000 words. Restructure with commas,
parentheses, or separate sentences instead. This is the most widely known
tell, and readers now flinch at a single one.

**Colon punchiness.** Do not compensate for the em-dash rule with "X: Y"
constructions ("This is the answer: a simpler approach"). Colons are for
genuine lists. Semicolons should be rare.

**Semicolon chains.** A related tell is the enumeration strung across one
sentence with semicolons: "it leases a machine; syncs your files; runs
the command; streams output; records evidence". Break it into sentences,
each of which says something about its step.

## Sentence patterns

**Contrast rhetoric.** "It is not X, it is Y", "X, not Y", "not X, but Y"
and all variants are banned. The construction forces the reader to hold a
clause (X) that the sentence immediately throws away. Say Y directly.

- Bad: "It is not a benchmark predictor. It is a roofline."
  Good: "It is a roofline."
- Bad: "This changes the packaging, not the position."
  Good: "The position stays the same."
- Bad: "Queries hit the disk, not GitHub."
  Good: "Queries hit the local database, so no GitHub quota is spent."

A plain negation is fine when the negation is the content: a genuine
non-equivalence ("fitting in memory does not imply serving usefully"), a
disambiguation between two real quantities, or a warning about a real
misconception. Use it once, plainly, without the paired "it is Y" reveal.

**"Not just X" escalation.** "It isn't just X, it's Y" and similar
intensifier patterns are banned for the same reason.

**Rule of three.** Lists of exactly three parallel items, sentence after
sentence, are a strong tell. In measured corpora, AI copy produces these
at several times the human rate. Vary list length, or use fewer lists.

**Anaphora chains.** "No client ID, no redirect URI, no developer
dashboard." Three parallel negations in a row read as ad copy. One plain
sentence saying what the reader skips is stronger.

**Fragment rhythm.** AI copy alternates verbless two-to-four word punches
("Actively developed.", "Two jobs, one binary.") with thirty-word feature
enumerations. Human short sentences are full clauses with a subject and a
verb. If a paragraph swings between fragments and freight trains, rewrite
it into sentences of ordinary, varied length.

**Hedging boilerplate.** Cut "it's worth noting that", "it's important to
remember", and similar throat-clearing.

**Overwrought transitions.** Cut "moreover", "furthermore", "in
conclusion", and summary paragraphs that restate what was just said.

**Inflated vocabulary.** Use the plain word: "delve", "landscape",
"testament to", "tapestry", "crucial", and "leverage" as a verb all mark
generated text.

## Openings

Say what the thing is before saying what it does. GPT-flavored copy
describes behavior and dodges identity, so the reader has to assemble
what kind of thing they are looking at. State the category in the first
sentence and the practical job in the second.

- Bad: "LocalPerf benchmarks local LLM inference servers and keeps the
  evidence in one portable run artifact."
- Good: "LocalPerf is a local LLM inference benchmark CLI. It runs
  benchmark plans against local inference servers and stores the
  evidence in one portable run artifact."

The identity sentence has degraded forms that do not count:

- The headless fragment: "A local-first GitHub triage tool for
  maintainers." Category information with no subject and no verb.
- The buried identity: opening with an imperative benefit ("Keep your
  editor and git workflow.") and stating what the tool is three screens
  down.
- Pseudo-identity: "is designed to be the layer between X and Y" states
  purpose, and "root() is the product" is a meta-remark. Neither names a
  category.

The same rule scales up: a section or report should open with sentences
that orient the reader (what this is, what was done, what follows), never
with a compressed context dump. See "Page structure" below.

## Headings

Make headings labels, not sentences. A heading names the topic of its
section as a noun phrase ("Capacity limit", "Crash testing", "Worked
examples") so the reader can scan the structure. Specific heading tells:

- **Slogan headings.** A full subject-verb heading ("Capacity Caps the
  Batch") pre-empts the section and reads as a pitch.
- **Comma couplets.** The parallel two-beat slogan ("Local loop, remote
  box", "Two jobs, one binary", "Many providers, one loop") is among the
  strongest title-level tells and appears almost exclusively in
  generated copy.
- **Imperative slogans.** "Pick your path", "Try it", "Reuse what's
  warm". These sell the section instead of naming it.
- **Rhetorical frames.** A run of "Why X" / "How Y" / "What you get"
  headings down one outline is a smell, and so is any one template
  stamped across siblings ("I want to try it / I want to wire up an
  agent / I want the full reference").

Use sentence case. Capitalize the first word, proper nouns, and coined
terms; lowercase the rest ("Memory-fit batch", never "The Memory-Fit
Batch"). Keep acronyms uppercase. Do not make "The" a reflexive prefix;
drop it from noun-phrase labels ("The capacity limit" becomes "Capacity
limit") and keep it only where a full clause needs it.

The exception is a deliberate major statement. A heading may be a full
sentence when that sentence is a load-bearing claim the section exists to
defend, such as a named law or a thesis. Use it rarely; in a document
whose headings are otherwise noun phrases, a sentence heading should earn
its emphasis, and two in a row almost never do.

After drafting, read the headings as a flat list and check that they are
the same kind of thing: labels with labels, one register, one casing.

## Page structure

**Subtitles where intros belong.** A section that opens with compressed
context fragments ("Six pages against three baselines. Code blocks
stripped; rates per 1,000 words.") has skipped the introduction. The
reader gets metadata before they know what the document is about. Write
an intro in full sentences that says what this is, what was done, and
what the reader will find, in that order. Details the reader cannot use
yet belong later, next to where they matter.

**Labeled-bullet walls.** The bullet shaped "Label — one-sentence
elaboration" (or "Label. Elaboration.") is the signature layout unit of
AI landing copy; measured pages are 50 to 95 percent this one shape,
while human docs almost never use it. A run of them is a wall of parallel
fragments, and none of them explains anything. Convert runs into prose
paragraphs that connect the items, and keep bullets for genuinely
enumerable things. Vary their shape when you do use them.

**Formula and fact dumps.** No section may become a list of statements
one after another, whether formulas, definitions, or feature claims.
Introduce each item with prose that says why it appears, and follow
substantial items with prose that interprets them. Long derivations or
arguments must be broken into stages with the goal stated between stages.
The reader should be able to follow the conceptual path from the
surrounding paragraphs alone.

**Template stamping.** The same skeleton shipped across documents ("Why
X", "Pick your path", "Status", "Out of scope", a "five minutes"
time-to-value promise) marks a house style produced by one prompt. Any
single page looks fine; side by side they are unmistakable. Let each
document's structure follow its content.

**Word diarrhea.** Do not pad with exhaustive feature taxonomies,
implementation internals, long option catalogs, or process history the
reader does not need for the task at hand. Being comprehensive about the
wrong things is a tell of its own.

**Emoji feature grids.** The grid of emoji-headed feature cards is the
most recognizable generated landing-page layout. Do not use emojis as
section markers or bullets at all.

**Manual heading numbers.** Do not number Markdown headings by hand
("## 1. Overview"). Let the renderer or publication system number
sections when numbering is needed.

## Repetition and word choice

Generated text avoids repeating itself: each mention of a thing gets a
fresh synonym, which pushes lexical variety above the human range. Human
writers repeat deliberately. They reuse the established term for a
concept instead of rotating synonyms, and they repeat a phrase for
emphasis when hammering a point. Keep one name per concept through a
document, and let purposeful repetition stand.

The same applies to sentence shape in reverse: humans vary rhythm
naturally, while generated text stamps one shape (or one bullet template)
many times. Uniform novelty in words plus uniform sameness in structure
is the combination to break up.

## Final sweep

Before finishing any writing task, check the draft against this list:

- Em dashes within budget; no "X: Y" punch lines; no semicolon chains.
- No contrast rhetoric or "not just X" anywhere.
- No run of exactly-three lists; no anaphora chains.
- No verbless fragments doing a sentence's job.
- The document says what its subject is before what it does.
- Sections open with orienting sentences, never context-dump fragments.
- Headings are sentence-case noun-phrase labels; no slogans, comma
  couplets, imperatives, or repeated rhetorical frames.
- No labeled-bullet walls; bullets vary in shape and are genuinely lists.
- No hedging, inflated vocabulary, or restating summaries.
- One name per concept; repetition only where it serves emphasis.

When editing existing text, fix a smell by restructuring the sentence or
the section. Swapping one banned pattern for another (an em dash for a
punchy colon, a triad for an anaphora chain) changes nothing.
