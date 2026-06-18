---
name: manage-repos
description: Use when creating, onboarding, auditing, or tightening GitHub repositories, especially applying github-sane-defaults to every repository and adding stricter branch rulesets that require human review before merges to the default branch.
---

# Manage Repos

## Core Rule

Apply `github-sane-defaults` to every GitHub repository you create or manage:

```sh
npx -y github-sane-defaults@latest apply OWNER/REPO
```

For an entire organization:

```sh
npx -y github-sane-defaults@latest apply OWNER --all
```

Use `plan` first when auditing or when the user has not explicitly approved changes:

```sh
npx -y github-sane-defaults@latest plan OWNER/REPO
```

## Slophammer

When creating or onboarding a project in a language supported by Slophammer,
apply Slophammer standards too. The point is not a one-off local scan; add the
checker/config/CI so the repository keeps enforcing the standard.

Supported checker selection:

- Go: `slophammer-go`
- TypeScript: `slophammer-ts`
- Rust: `slophammer-rs`
- Python: `slophammer-py`

Start from the Slophammer agent entrypoint:

```text
https://github.com/dutifuldev/slophammer/blob/main/docs/AGENT_ENTRYPOINT.md
```

Typical new-repo tasks:

- add `AGENTS.md` with the commands agents must run before finishing
- add `slophammer.yml`
- add or update CI so the selected Slophammer checker runs
- pin the checker version in CI
- run the selected checker locally and report whether it passed

Do not claim Slophammer passed if the language-specific checker is unavailable.
In that case, apply the documented standards manually and say what could not be
run.

## Strict Merge Review

Some repositories need a stricter rule: an agent may have write access, but must
not be able to merge to the default branch just because it wants to. For those
repositories, create an additional branch ruleset that:

- targets `~DEFAULT_BRANCH`
- requires one approving pull request review
- allows bypass only for organization admins
- does not grant bypass to write, maintain, or repository-admin roles

This strict rule complements `github-sane-defaults`; it does not replace it.

Example `gh` command:

```sh
OWNER="example-org"
REPO="example-repo"
RULESET_NAME="strict: require review before default-branch merge"
payload_file="$(mktemp)"

jq -n --arg name "$RULESET_NAME" '{
  name: $name,
  target: "branch",
  enforcement: "active",
  bypass_actors: [
    { actor_id: null, actor_type: "OrganizationAdmin", bypass_mode: "always" }
  ],
  conditions: {
    ref_name: { include: ["~DEFAULT_BRANCH"], exclude: [] }
  },
  rules: [
    {
      type: "pull_request",
      parameters: {
        required_approving_review_count: 1,
        dismiss_stale_reviews_on_push: false,
        required_reviewers: [],
        require_code_owner_review: false,
        require_last_push_approval: false,
        required_review_thread_resolution: false,
        allowed_merge_methods: ["merge", "squash", "rebase"]
      }
    }
  ]
}' >"$payload_file"

ruleset_id="$(
  gh api "repos/$OWNER/$REPO/rulesets" --jq \
    ".[] | select(.name == \"$RULESET_NAME\") | .id" | head -n 1
)"

if [ -n "$ruleset_id" ]; then
  gh api -X PUT "repos/$OWNER/$REPO/rulesets/$ruleset_id" \
    --input "$payload_file"
else
  gh api -X POST "repos/$OWNER/$REPO/rulesets" \
    --input "$payload_file"
fi

rm -f "$payload_file"
```

## Workflow

1. Identify the target repository or organization using `gh repo view` or the
   user-provided target.
2. Run `github-sane-defaults plan` unless the user already asked to apply.
3. Run `github-sane-defaults apply` for every target repository.
4. For supported languages, add Slophammer configuration and CI.
5. For strict repositories, create or update the separate review-required
   ruleset with organization-admin-only bypass.
6. Verify GitHub rulesets with:

```sh
gh api "repos/OWNER/REPO/rulesets" --jq '.[] | {name, target, enforcement}'
```

For the strict ruleset, fetch the full payload and confirm `pull_request`
requires one approval and `bypass_actors` contains only `OrganizationAdmin`.

## Safety

- Do not put personal names, private usernames, credentials, or local machine paths
  into reusable skill docs, ruleset names, or example commands.
- Do not weaken an existing stricter rule unless the user explicitly asks.
- Do not give bypass to agent accounts, write-role actors, maintain-role actors,
  or broad repository-admin roles for organization repositories.
- If the target is a personal repository without organization admins, stop and
  ask before choosing a different bypass model.
