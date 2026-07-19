# OnurPi

Onur Solmaz's Pi extensions and global configuration.

## Packages

- [`@onurpi/turn-fold`](packages/turn-fold/): turn-level transcript folding that preserves the final
  response.
- [`pi-tui-history-replay`](packages/pi-tui-history-replay/): vendored full visible branch history
  across context compaction.

## Global settings

[`settings.json`](settings.json) is the source-controlled copy of the global Pi settings at
`~/.pi/agent/settings.json`. Pi authentication, session history, trust decisions, and model-provider
state remain outside this repository. Review settings for credentials or machine-specific values
before committing future changes.

Update the tracked copy after changing Pi settings:

```bash
cp ~/.pi/agent/settings.json agents/onurpi/settings.json
```

Apply the tracked settings on another machine from the tools repository root:

```bash
cp agents/onurpi/settings.json ~/.pi/agent/settings.json
```

## Structure

Each extension is an independent package under `packages/` with its own `package.json`, entry point,
tests, and README. Package manifests declare Pi entry points through `pi.extensions`; the private
root manifest also registers them for workspace-wide development.

This workspace follows the package-directory structure used by
[`ogulcancelik/pi-extensions`](https://github.com/ogulcancelik/pi-extensions), while keeping shared
TypeScript quality tooling at the workspace root.

## Development

```bash
npm install
npm run check
npm run mutate
npm run slophammer
```

Quick-test an extension without installing it permanently:

```bash
pi -e .
```
