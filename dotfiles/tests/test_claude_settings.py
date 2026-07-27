from __future__ import annotations

import importlib.machinery
import importlib.util
import json
import stat
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SCRIPT = Path(__file__).parents[1] / "scripts" / "claude-settings"
LOADER = importlib.machinery.SourceFileLoader("claude_settings", str(SCRIPT))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
assert SPEC is not None
CLAUDE_SETTINGS = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(CLAUDE_SETTINGS)


class ClaudeSettingsTest(unittest.TestCase):
    def test_backup_and_install_round_trip_with_portable_home(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            source_home = root / "source-home"
            target_home = root / "target-home"
            repo_settings = root / "repo" / "claude" / "settings.json"
            source = source_home / ".claude" / "settings.json"
            source.parent.mkdir(parents=True)
            source.write_text(
                json.dumps(
                    {
                        "hooks": {
                            "SessionStart": [
                                {"command": f"{source_home}/bin/session-hook"}
                            ]
                        },
                        "permissions": {"defaultMode": "auto"},
                    }
                ),
                encoding="utf-8",
            )

            with patch.object(CLAUDE_SETTINGS, "REPO_SETTINGS", repo_settings):
                CLAUDE_SETTINGS.backup(source_home)
                portable = json.loads(repo_settings.read_text(encoding="utf-8"))
                self.assertEqual(
                    portable["hooks"]["SessionStart"][0]["command"],
                    "__HOME__/bin/session-hook",
                )
                CLAUDE_SETTINGS.install(target_home)

            installed = target_home / ".claude" / "settings.json"
            restored = json.loads(installed.read_text(encoding="utf-8"))
            self.assertEqual(restored["permissions"]["defaultMode"], "auto")
            self.assertEqual(
                restored["hooks"]["SessionStart"][0]["command"],
                f"{target_home}/bin/session-hook",
            )
            self.assertEqual(stat.S_IMODE(installed.stat().st_mode), 0o600)

    def test_backup_rejects_secret_environment_values(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            root = Path(temporary_directory)
            home = root / "home"
            repo_settings = root / "repo" / "claude" / "settings.json"
            source = home / ".claude" / "settings.json"
            source.parent.mkdir(parents=True)
            source.write_text(
                json.dumps({"env": {"ANTHROPIC_API_KEY": "secret-value"}}),
                encoding="utf-8",
            )

            with (
                patch.object(CLAUDE_SETTINGS, "REPO_SETTINGS", repo_settings),
                self.assertRaisesRegex(ValueError, "env.ANTHROPIC_API_KEY"),
            ):
                CLAUDE_SETTINGS.backup(home)
            self.assertFalse(repo_settings.exists())

    def test_settings_root_must_be_an_object(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_directory:
            path = Path(temporary_directory) / "settings.json"
            path.write_text("[]\n", encoding="utf-8")
            with self.assertRaisesRegex(TypeError, "JSON object"):
                CLAUDE_SETTINGS.load_settings(path)


if __name__ == "__main__":
    unittest.main()
