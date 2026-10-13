-- Cycle Ghostty theme: ctrl+opt+cmd+T (global, fires in any app).
-- Alerts with the new theme name so the switch is visible. Ghostty skips
-- the reload signal while it is the focused app, so if the windows do not
-- update, press cmd+shift+, in Ghostty or refocus another app and back.
hs.hotkey.bind({"ctrl", "alt", "cmd"}, "t", function()
  local out, ok = hs.execute("/Users/onur/.local/bin/ghostty-theme --cycle 2>&1")
  local name = out:match("Switched to '([^']+)'")
  if name then
    hs.alert.show("Ghostty theme: " .. name)
  else
    hs.alert.show("ghostty-theme failed: " .. (out ~= "" and out or "no output"))
  end
end)

hs.alert.show("Hammerspoon: theme hotkey active")
