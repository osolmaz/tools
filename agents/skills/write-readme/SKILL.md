---
name: write-readme
description: Use when creating, rewriting, or reviewing README files. Keeps README content focused on users: what to install, how to use it, and what not to include from maintainer release process.
---

# Write README

Use this skill when writing or reviewing README content.

The README is for users. Put install and usage information there.

Do not put maintainer release details in the README unless the repo is specifically about releases.

For package or CLI READMEs, show the package users should install and the command they should run:

```text
npm install -g slophammer-ts
slophammer-ts check .
slophammer-ts rules
slophammer-ts dry .
```

Keep release-process details out of user README files:

- OIDC setup
- npm trusted publishing
- provenance
- release workflow names
- tag instructions
- "first release" history

Put those in maintainer docs if they need to exist.
