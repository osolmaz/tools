---
name: write-readme
description: Use when creating, rewriting, or reviewing README files for repositories, packages, CLIs, libraries, apps, or monorepos. Keeps user-facing README content focused on what the project is, how to install it, how to use it, and what users need to know, while moving maintainer-only release/process details elsewhere.
---

# Write README

Use this skill when writing or reviewing README content.

The README is for users first. It should help someone decide whether the project is relevant, install it, run it, and understand the main commands or API. It should not become a release diary, maintainer checklist, or CI/OIDC setup guide unless the repository is specifically a release-process tool.

## Workflow

1. Read the existing README, package metadata, CLI help, and nearby docs before editing.
2. Identify the README audience:
   - root repo README: project overview, install paths, common usage, repo layout when useful
   - package README: package-specific install and usage
   - app README: run, configure, and deploy enough to use it
   - maintainer docs: release workflows, credentials, tags, CI internals, operational history
3. Put user-facing content in the README.
4. Move maintainer-only details to `CONTRIBUTING.md`, `docs/`, release docs, or workflow comments.
5. Remove stale status language after releases or package changes.
6. Run the repo's docs checks and grep for stale wording before finishing.

## What Belongs In A README

- one plain sentence that says what the project or package does
- install commands users can run now
- quick-start commands with realistic paths or arguments
- the package name and executable name when they differ
- the smallest useful command/API examples
- expected output or exit behavior when that helps users
- links to deeper docs instead of copying maintainer detail inline
- current status only when it affects users

## What Does Not Belong

Keep these out of user-facing README sections:

- OIDC, trusted publishing, provenance setup, npm publisher configuration
- exact release workflow names, tag-push procedures, or CI implementation notes
- "first release", "workflow-published", or chronological release history
- stale claims like "private", "not published", or "publishing is deferred"
- internal package reservation details unless users need them to choose the right install command
- long maintainer acceptance checklists

If the information is still useful, move it to a maintainer doc and link only when users need that path.

## Package And CLI Guidance

For npm CLIs, show the install and the executable:

```sh
npm install -g package-name
command-name check .
command-name --help
```

If `npx` is a good path, include it:

```sh
npx package-name command .
```

If a generic package name is reserved for a future umbrella/default installer, do not make that the main story. Say briefly which package users should install today, then continue with usage.

For monorepos, keep the root README broad and put package-specific usage in each package README. The package README should not force users to understand the repository release machinery.

## Review Checklist

Before finishing, scan for:

```sh
rg -n "trusted publishing|provenance|OIDC|workflow|tag shape|first release|not published|publishing is deferred|private|manual publish" README.md docs package*/README.md
```

Keep matches only when they are in maintainer docs or are clearly needed by users.

Then run the nearest docs formatter/checker and any package README validation the repo already uses.
