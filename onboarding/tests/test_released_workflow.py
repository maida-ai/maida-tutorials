"""Replay the released onboarding CLI in an isolated, fresh user project.

This is protocol replay, not a claim that a live coding agent was exercised.
"""

import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
MAIDA = shutil.which("maida")
PYTHON = shutil.which("python")


class ReleasedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.environment = os.environ.copy()
        self.environment["HOME"] = str(self.project / "home")
        self.environment["MAIDA_DATA_DIR"] = str(self.project / "known-good")

    def command(self, *arguments, expected=0, payload=None):
        result = subprocess.run(
            [MAIDA, *arguments],
            cwd=self.project,
            env=self.environment,
            input=None if payload is None else json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
        )
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def capture(self, session, *, failing=False):
        payload = {
            "session_id": session,
            "cwd": str(self.project),
            "transcript_path": str(self.project / "local-transcript.jsonl"),
        }
        events = [
            {"hook_event_name": "SessionStart", "source": "startup"},
            {
                "hook_event_name": "PreToolUse",
                "tool_name": "Bash" if failing else "Read",
                "tool_use_id": "read-1",
                "tool_input": {"file_path": "README.md"},
            },
            {
                "hook_event_name": "PostToolUse",
                "tool_name": "Bash" if failing else "Read",
                "tool_use_id": "read-1",
                "tool_input": {"file_path": "README.md"},
                "tool_response": {"success": True},
            },
        ]
        if failing:
            events += [
                {
                    "hook_event_name": "PreToolUse",
                    "tool_name": "Bash",
                    "tool_use_id": "test-1",
                    "tool_input": {"command": "project-test-command"},
                },
                {
                    "hook_event_name": "PostToolUseFailure",
                    "tool_name": "Bash",
                    "tool_use_id": "test-1",
                    "tool_input": {"command": "project-test-command"},
                    "error": "test failed",
                },
            ]
        events.append({"hook_event_name": "SessionEnd", "reason": "other"})
        for event in events:
            result = self.command("capture", "claude-hook", payload=payload | event)
            self.assertEqual(result.stdout, "")

    def test_capture_review_pass_fail_and_repair(self):
        installation = subprocess.run(
            [
                PYTHON,
                str(ROOT / "onboarding/install_capture.py"),
                "--project",
                str(self.project),
                "--apply",
            ],
            env=self.environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(installation.returncode, 0, installation.stderr)
        self.capture("known-good-session")
        self.command("list")
        self.command("assert", "--expect-status", "ok", "--no-loops", "--no-guardrails")
        self.command("init", "--from-run", "latest")
        review = json.loads((self.project / ".maida/starter/review.json").read_text())
        self.assertTrue(review["review_required"])
        self.assertFalse((self.project / ".maida/policy.yaml").exists())
        starter = self.project / ".maida/starter/policy.yaml"
        candidate = yaml.safe_load(starter.read_text())
        candidate["metrics"]["required_tools"] = {"kind": "invariant", "all_of": ["Read"]}
        starter.write_text(yaml.safe_dump(candidate))
        self.command("init", "--reviewed", "--reason", "This task must read its configuration")
        policy = self.project / ".maida/policy.yaml"
        baseline = self.project / ".maida/baselines/agent.json"
        original_baseline = baseline.read_bytes()

        def gate(expected):
            result = self.command(
                "assert", "--baseline", str(baseline), "--policy", str(policy),
                "--format", "json", expected=expected,
            )
            return json.loads(result.stdout)

        self.assertTrue(gate(0)["passed"])
        self.environment["MAIDA_DATA_DIR"] = str(self.project / "candidate")
        self.capture("broken-session", failing=True)
        failing = gate(1)
        self.assertFalse(failing["passed"])
        self.assertIn("required_tools", json.dumps(failing))
        self.environment["MAIDA_DATA_DIR"] = str(self.project / "repaired")
        self.capture("repaired-session")
        self.assertTrue(gate(0)["passed"])
        self.assertEqual(baseline.read_bytes(), original_baseline)
        self.assertFalse((self.project / "home/.maida").exists())

    def test_init_rejects_mixed_and_duplicate_observations(self):
        self.capture("one-session")
        self.capture("another-session")
        ids = [path.parent.name for path in (self.project / "known-good/runs").glob("*/meta.json")]
        self.assertEqual(len(ids), 2)
        mixed = self.command("init", "--from-run", ids[0], "--from-run", ids[1], expected=2)
        self.assertIn("same workflow", mixed.stderr)
        duplicate = self.command("init", "--from-run", ids[0], "--from-run", ids[0], expected=2)
        self.assertIn("duplicate runs", duplicate.stderr)
        self.assertFalse((self.project / ".maida/policy.yaml").exists())

    def test_empty_evidence_does_not_look_like_activation(self):
        result = self.command("init", "--from-run", "latest", expected=2)
        self.assertTrue(result.stderr.strip())
        self.assertFalse((self.project / ".maida/policy.yaml").exists())
        self.assertFalse((self.project / ".maida/starter").exists())


if __name__ == "__main__":
    unittest.main()
