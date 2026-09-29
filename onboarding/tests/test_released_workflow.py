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
        self.command("extract", "--window", "known-good/runs", "--out", ".maida/draft")
        draft = json.loads((self.project / ".maida/draft/draft.json").read_text())
        self.assertTrue(draft["review_required"])
        self.assertFalse((self.project / ".maida/policy.yaml").exists())
        self.command("baseline", "--out", ".maida/baselines/coding-task.json")
        policy = self.project / ".maida/policy.yaml"
        policy.write_text(
            "version: 2\nmetrics:\n  required_tools: {kind: invariant, all_of: [Read]}\n  stop_condition_reached: {kind: invariant, require: true}\n"
        )
        original_baseline = (
            self.project / ".maida/baselines/coding-task.json"
        ).read_bytes()

        def gate(window, expected):
            result = subprocess.run(
                [
                    PYTHON,
                    str(ROOT / "onboarding/gate_capture.py"),
                    "--window",
                    window,
                    "--baseline",
                    ".maida/baselines/coding-task.json",
                    "--policy",
                    ".maida/policy.yaml",
                    "--same-task",
                    "--format",
                    "json",
                ],
                cwd=self.project,
                env=self.environment,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
            return json.loads(result.stdout)

        passing = gate("known-good/runs", 0)
        self.assertEqual(passing["verdict"], "pass")
        self.environment["MAIDA_DATA_DIR"] = str(self.project / "candidate")
        self.capture("broken-session", failing=True)
        failing = gate("candidate/runs", 1)
        self.assertEqual(failing["verdict"], "fail")
        self.assertIn("required_tools", json.dumps(failing))
        mapping = failing["capture_task_comparison"]
        self.assertNotEqual(
            mapping["baseline_source_run_name"], mapping["candidate_source_run_name"]
        )
        self.environment["MAIDA_DATA_DIR"] = str(self.project / "repaired")
        self.capture("repaired-session")
        self.assertEqual(gate("repaired/runs", 0)["verdict"], "pass")
        self.assertEqual(
            (self.project / ".maida/baselines/coding-task.json").read_bytes(),
            original_baseline,
        )
        self.assertFalse((self.project / "home/.maida").exists())

    def test_gate_refuses_ambiguous_sessions_without_modifying_evidence(self):
        self.capture("baseline")
        self.command("baseline", "--out", "baseline.json")
        (self.project / "policy.yaml").write_text(
            "version: 2\nmetrics:\n  required_tools: {kind: invariant, all_of: [Read]}\n"
        )
        self.environment["MAIDA_DATA_DIR"] = str(self.project / "candidate")
        self.capture("one-session")
        self.capture("another-session")
        command = [
            PYTHON,
            str(ROOT / "onboarding/gate_capture.py"),
            "--window",
            "candidate/runs",
            "--baseline",
            "baseline.json",
            "--policy",
            "policy.yaml",
        ]
        for flags, expected in (
            ([], "--same-task"),
            (["--same-task"], "multiple sessions"),
        ):
            result = subprocess.run(
                command + flags,
                cwd=self.project,
                env=self.environment,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
            self.assertIn(expected, result.stderr)

    def test_empty_evidence_does_not_look_like_activation(self):
        (self.project / "empty").mkdir()
        result = self.command(
            "extract", "--window", "empty", "--out", ".maida/draft", expected=2
        )
        self.assertIn("Invalid extraction input", result.stderr)
        self.assertFalse((self.project / ".maida/policy.yaml").exists())
        self.assertFalse((self.project / ".maida/draft").exists())


if __name__ == "__main__":
    unittest.main()
