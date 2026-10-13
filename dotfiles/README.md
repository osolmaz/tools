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

## Ghostty theme switching

`scripts/ghostty-theme` switches the Ghostty theme live: run it with no
arguments to browse themes, with a theme name to switch, or `--cycle` to
rotate through a fixed list. A Hammerspoon hotkey, ctrl+opt+cmd+T, runs
`ghostty-theme --cycle` from any app.

```sh
make install-ghostty install-hammerspoon
```

This installs the Ghostty config from `ghostty/`, the switcher script to
`~/.local/bin/ghostty-theme`, and the hotkey from `.hammerspoon/init.lua`.
The `theme` line in `ghostty/common.ghostty` records the last selected theme,
so it changes whenever the hotkey cycles. `make copy` refreshes it from the
live config.

## Recording mode

`scripts/record-mode` starts the video recording environment: a separate
Ghostty window with the Catppuccin Mocha theme and an isolated Herdr session,
plus the option to hide the Dock and desktop icons and open a clean Chrome
profile. `scripts/herdr-recording` is the launcher that window runs.

```sh
make install-recording-mode
record-mode start
```

`record-mode restore` brings the Dock and desktop icons back. The recorded
workflow and the design rules are documented in the `yt-recording-mode` skill
in the `osolmaz/agents` repository.

The Claude backup stores `~/.claude/settings.json` at
`claude/settings.json`. It replaces the home directory with a portable token
and refuses to copy likely credentials. Credentials and session data are never
included.
