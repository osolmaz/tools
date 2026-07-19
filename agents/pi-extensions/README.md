# Pi Extensions

Pi extensions developed in the tools repository.

## Packages

- [`pi-turn-fold`](packages/pi-turn-fold/): turn-level transcript folding that preserves the final
  response.
- [`pi-tui-history-replay`](packages/pi-tui-history-replay/): full visible branch history across
  context compaction.

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
