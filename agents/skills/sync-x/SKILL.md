---
name: sync-x
description: Sync Onur's X posts from xTap into xtap-store and the blog, then manually curate homepage featured posts. Use when asked to run or update the X/blog sync workflow, including from either the blog repo or the xtap-store repo.
---

# sync-x

## Purpose

Sync X posts from xTap, update the blog's generated X pages, and curate homepage featured posts manually.

## Invocation Rule

When invoked for a sync run, execute all relevant steps from beginning to end in one go:
- Resolve repo context
- Sync xTap archive when starting from `xtap-store`
- Sync the blog
- Manually curate featured JSON
- Apply + validate
- PR handling
- Final report

Do not stop halfway or do partial execution unless the user explicitly asks to stop.

## Repo Context

First identify the current repository:

- Blog repo: contains `_scripts/sync_xtap_tweets.ts`, `_data/x/homepage_featured.json`, and `Makefile` targets `sync-x` / `sync-x-raw`.
- xTap store repo: contains `go.mod` with module `xtap-store` and `cmd/xtap-store/main.go`.

Default known paths:

- Blog repo: `/home/bob/offline/blog`
- xTap store repo: `/home/bob/xtap-store`
- xTap source directory: `$HOME/Downloads/xtap`

If invoked from the blog repo, run the blog workflow directly.

If invoked from the xTap store repo:

1. Run the xTap store sync from that repo first:

```bash
go run ./cmd/xtap-store sync --source "$HOME/Downloads/xtap" --repo .
```

2. Check the store result:

```bash
go run ./cmd/xtap-store verify --source "$HOME/Downloads/xtap" --repo .
git status --short
```

3. Switch to the blog repo and run the blog workflow:

```bash
cd /home/bob/offline/blog
make sync-x
```

Do not run `make sync-x` in `xtap-store`; it is a Go repository and does not own the blog `make` targets.

## Files

Blog repo:

- Sync script: `_scripts/sync_xtap_tweets.ts`
- Featured config: `_data/x/homepage_featured.json`
- Validator: `_scripts/validate_x_homepage_featured.ts`
- Home feed renderer: `_layouts/home.html`
- Social media rules: `docs/SOCIAL_MEDIA_STRATEGY.md`

xTap store repo:

- CLI: `cmd/xtap-store/main.go`
- Sync logic: `internal/store/sync.go`
- Managed archive: `data/tweets/YYYY/MM/tweets-YYYY-MM-DD.jsonl`

## Step 1: Sync My Posts + What I Quote

From the blog repo, run:

```bash
make sync-x
```

This sync should:
- import from xTap capture files
- keep your own posts and quoted-post context needed by your posts
- exclude unrelated non-owner posts from the raw archive subset
- split raw archive into day files using each tweet `created_at` date
- regenerate `_tweets/*.md` pages from synced data
- keep homepage/date routing derived from tweet timestamps
- avoid manual date mapping

If needed, regenerate from committed raw archive only:

```bash
make sync-x-raw
```

## Step 2: Generate Featured JSON Manually

Edit `_data/x/homepage_featured.json` by reading posts one by one.
Also read `docs/SOCIAL_MEDIA_STRATEGY.md` and apply its editorial rules during this pass.

Rules:
- do not auto-generate featured decisions
- do not bulk-assign titles
- read each candidate post manually, then decide `featured: true/false` and `hidden: true/false`
- only use `hidden: true` for clear violations of `docs/SOCIAL_MEDIA_STRATEGY.md`
- do not invent any hide criteria outside `docs/SOCIAL_MEDIA_STRATEGY.md`
- if a post is within the approved topics and passes the strategy checklist, keep `hidden: false`
- use `featured: false` and `hidden: false` for ordinary allowed posts that are not homepage-worthy
- if a post does not follow `docs/SOCIAL_MEDIA_STRATEGY.md`, set `hidden: true`
- when setting `hidden: true`, also set `featured: false`
- when setting `hidden: true`, set `hide_reason` to the exact violated line from `docs/SOCIAL_MEDIA_STRATEGY.md`
- if no exact strategy line clearly applies, keep `hidden: false`
- if a hide decision depends on ambiguous tone or intent, default to `hidden: false`
- when changing a post from hidden back to visible, clear `hide_reason`
- when setting `hidden: true`, leave `title: ""` unless the user explicitly asks otherwise
- if featured, set a title according to the title rules below
- keep this step as human editorial work, not script-driven
- ensure every synced owner post is represented in `_data/x/homepage_featured.json`
- for any owner post missing in config, add `featured: false`, `hidden: false`, and `title: ""`
- only set `featured: true` after manual one-by-one review
- do not set both `featured: true` and `hidden: true`

### What qualifies as hidden

- clear violations of `docs/SOCIAL_MEDIA_STRATEGY.md` only
- examples: off-topic/random posts, politics, toxic or swearword-heavy posts, posts that sound secret/internal/private, posts that imply insider information without a safe public basis, or posts that blur personal views with official OpenClaw communication
- do not hide a post merely because it is short, fragmentary, repetitive, routine, not insightful enough, or not strong enough to feature
- AI-related, developer-tools, and OpenClaw-related posts are not hide candidates by default if they fit the strategy file
- `not featured` is not the same as `hidden`
- when hidden, the reason must be auditable from the strategy file without interpretation drift

### What qualifies as featured

- thoughtpiece-style posts only
- long commentary with at least 2-3 paragraphs
- not short quips, routine updates, reactions, direct retweets, or fragment posts

### Title rules

- use short, plain language
- use roughly 4-12 words
- state what the post is about
- capture the underlying point, not full tweet text
- if the post has a striking punchline or sentence that works well as a title, use that line directly
- avoid clickbait
- avoid rhetorical or question-hook style
- do not use `A: B` format
- avoid hashtags and handles unless essential

Config schema:

```json
{
  "version": 1,
  "posts": [
    {
      "tweet_id": "2027686423873073172",
      "featured": true,
      "hidden": false,
      "title": "Agentic Engineering needs rigor, not just intuition"
    },
    {
      "tweet_id": "2026621786226331830",
      "featured": false,
      "hidden": true,
      "title": "",
      "hide_reason": "No politics."
    }
  ]
}
```

Field rules:
- `tweet_id`: numeric string
- `featured`: boolean
- `hidden`: optional boolean; when `true`, omit the post from generated site output entirely
- `hide_reason`: optional string; required and non-empty when `hidden` is `true`, and absent or empty when `hidden` is `false`
- `title`: optional string; if empty on a featured post, homepage falls back to the first tweet line
- `featured` and `hidden` must not both be `true`
- never store date in config; derive date from tweet timestamp

## Apply + Validate

After editing featured config:

```bash
make validate-x-featured
make sync-x-raw
```

If the run began in `xtap-store`, also confirm the store repo is clean or only contains expected archive changes handled by `xtap-store sync`.

## Step 3: PR Handling

After blog changes are ready:

- look for open PRs related to X sync or featured workflow changes
- if a matching open PR exists, apply new commits to that PR branch
- if no matching open PR exists, open a new branch and create a new PR that is ready for review, not a draft PR
- always share the PR link at the end

Practical check:

```bash
gh pr list --state open --limit 100
```

For `xtap-store` archive changes, prefer the repository's normal `xtap-store sync` commit/push behavior. If manual PR work is needed there, keep it separate from the blog PR and report both links.

## Step 4: Final Report

At the very end, always provide a report with:

- posts added in this sync run, each with a short content summary
- posts marked as `featured: true` in this run, each with title and short content summary
- posts marked as `featured: false` in this run, each with a short content summary
- posts marked as `hidden: true` in this run, each with exact hide reason and short content summary
- for each newly featured post, the exact title that was assigned, plus a short content summary
- if no posts were added or featured, explicitly say `none`

Use this exact output structure:

```md
Final Report

Posts added in this sync run
- <tweet_id> | <brief content summary>
- ...

Featured true in this run
- <tweet_id> | <title> | <brief content summary>
- ...

Featured false in this run
- <tweet_id> | <brief content summary>
- ...

Hidden true in this run
- <tweet_id> | <hide_reason> | <brief content summary>
- ...

Newly featured titles assigned
- <tweet_id> -> <exact title> | <brief content summary>
- ...
```

Formatting rules:
- keep section headers exactly as shown above
- include both `Featured true in this run` and `Featured false in this run` every time
- include `Hidden true in this run` every time
- when a section has no items, write `- none`
- in `Featured true in this run`, always include the title after `|` (use empty string if none)
- never output a bare ID without human-readable content after it
- the content summary should be the first line or a concise snippet of the actual post text, not a paraphrased label
- in `Hidden true in this run`, the `hide_reason` must quote the violated strategy line exactly

Notes:
- `featured` controls homepage only
- `hidden` removes a post entirely from generated site output
- tweets appear on date archive pages and `/x/...` pages only when they are not hidden
- full tweet content stays on `/x/...` pages only for non-hidden posts
- invalid or stale featured IDs should fail sync/validation early instead of silently drifting
