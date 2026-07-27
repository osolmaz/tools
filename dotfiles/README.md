# Dotfiles

## Installing on a new system

```sh
make install
```

## Backing up local settings

```sh
make copy
```

Claude Code settings can also be synchronized on their own:

```sh
make backup-claude
make install-claude
```

The Claude backup stores `~/.claude/settings.json` at
`claude/settings.json`. It replaces the home directory with a portable token
and refuses to copy likely credentials. Credentials and session data are never
included.
