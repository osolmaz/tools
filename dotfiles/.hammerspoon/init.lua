-- Cycle Ghostty theme: ctrl+opt+cmd+T (global, fires in any app)
hs.hotkey.bind({"ctrl", "alt", "cmd"}, "t", function()
  hs.execute("/Users/onur/.local/bin/ghostty-theme --cycle >/dev/null 2>&1 &")
end)

hs.alert.show("Hammerspoon: theme hotkey active")
