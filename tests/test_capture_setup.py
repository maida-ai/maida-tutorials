"""The onboarding installer must preserve the user's existing project setup."""

import json
import tempfile
import unittest
from pathlib import Path

from onboarding.install_capture import COMMAND, EVENTS, install, merged_settings


class CaptureSetupTests(unittest.TestCase):
    def test_preview_is_read_only_and_apply_is_idempotent(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            self.assertEqual(install(project, apply=False), list(EVENTS))
            self.assertFalse((project / ".claude").exists())
            self.assertEqual(install(project, apply=True), list(EVENTS))
            settings = project / ".claude/settings.json"
            before = settings.read_bytes()
            self.assertEqual(install(project, apply=True), [])
            self.assertEqual(settings.read_bytes(), before)

    def test_existing_hooks_permissions_and_other_settings_survive(self):
        original = {
            "permissions": {"deny": ["Write"]},
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Read",
                        "hooks": [{"type": "command", "command": "existing-observer"}],
                    }
                ]
            },
        }
        merged, added = merged_settings(original)
        self.assertEqual(merged["permissions"], original["permissions"])
        self.assertEqual(
            merged["hooks"]["PostToolUse"][0], original["hooks"]["PostToolUse"][0]
        )
        self.assertEqual(len(added), len(EVENTS))
        self.assertEqual(len(original["hooks"]["PostToolUse"]), 1)

    def test_matched_capture_does_not_hide_missing_unfiltered_capture(self):
        existing = {
            "hooks": {
                "PostToolUse": [
                    {
                        "matcher": "Read",
                        "hooks": [{"type": "command", "command": COMMAND}],
                    }
                ]
            }
        }
        merged, added = merged_settings(existing)
        self.assertIn("PostToolUse", added)
        self.assertEqual(len(merged["hooks"]["PostToolUse"]), 2)

    def test_invalid_settings_are_not_overwritten(self):
        for payload in (
            "invalid JSON",
            "[]",
            '{"hooks": []}',
            '{"hooks": {"SessionStart": [{}]}}',
        ):
            with (
                self.subTest(payload=payload),
                tempfile.TemporaryDirectory() as temporary,
            ):
                project = Path(temporary)
                (project / ".claude").mkdir()
                settings = project / ".claude/settings.json"
                settings.write_text(payload)
                with self.assertRaises(ValueError):
                    install(project, apply=True)
                self.assertEqual(settings.read_text(), payload)

    def test_symlinked_settings_are_not_followed(self):
        with tempfile.TemporaryDirectory() as temporary:
            project = Path(temporary)
            (project / ".claude").mkdir()
            other = project / "other.json"
            other.write_text("{}")
            (project / ".claude/settings.json").symlink_to(other)
            with self.assertRaises(ValueError):
                install(project, apply=True)
            self.assertEqual(json.loads(other.read_text()), {})


if __name__ == "__main__":
    unittest.main()
