"""Replay the released onboarding CLI in an isolated, fresh user project.

This is protocol replay, not a claim that a live coding agent was exercised.
"""

import json
import os
import pty
import shlex
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

import yaml

MAIDA = shutil.which("maida")


class ReleasedWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.project = Path(self.temporary.name)
        self.environment = os.environ.copy()
        self.environment["HOME"] = str(self.project / "home")
        self.environment["MAIDA_DATA_DIR"] = str(self.project / "data")
        self.environment.pop("CI", None)
        subprocess.run(
            ["git", "init", "--quiet", str(self.project)],
            env=self.environment,
            check=True,
        )
        (self.project / ".claude").mkdir()
        self.settings = self.project / ".claude/settings.local.json"
        self.original_settings = {"permissions": {"deny": ["Write"]}}
        self.settings.write_text(json.dumps(self.original_settings))

    def command(self, *arguments, expected=0, payload=None, approval=None):
        options = {"cwd": self.project, "env": self.environment, "text": True}
        if approval is None:
            result = subprocess.run(
                [MAIDA, *arguments],
                **options,
                input=None if payload is None else json.dumps(payload),
                capture_output=True,
                check=False,
                timeout=30,
            )
        else:
            # First-run setup requires an actual terminal before asking approval.
            master, slave = pty.openpty()
            try:
                with subprocess.Popen(
                    [MAIDA, *arguments],
                    **options,
                    stdin=slave,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                ) as process:
                    os.write(master, (approval + "\n").encode())
                    try:
                        stdout, stderr = process.communicate(timeout=30)
                    except subprocess.TimeoutExpired:
                        process.kill()
                        process.communicate()
                        raise
                    result = subprocess.CompletedProcess(
                        arguments, process.returncode, stdout, stderr
                    )
            finally:
                os.close(master)
                os.close(slave)
        self.assertEqual(result.returncode, expected, result.stdout + result.stderr)
        return result

    def capture(self, session, *, failing=False, looping=False, recovered=False):
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
        if failing or recovered:
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
        if looping:
            for index in range(3):
                tool = {
                    "tool_name": "Read",
                    "tool_use_id": f"loop-{index}",
                    "tool_input": {"file_path": "pyproject.toml"},
                }
                events.extend(
                    [
                        {"hook_event_name": "PreToolUse", **tool},
                        {
                            "hook_event_name": "PostToolUse",
                            "tool_response": {"content": "pytest"},
                            **tool,
                        },
                    ]
                )
        events.append({"hook_event_name": "SessionEnd", "reason": "other"})
        settings = json.loads(self.settings.read_text())
        for event in events:
            hook = settings["hooks"][event["hook_event_name"]][-1]["hooks"][0][
                "command"
            ]
            # Execute exactly the installed observer without uv's PATH.
            environment = self.environment | {"PATH": os.defpath}
            result = subprocess.run(
                shlex.split(hook),
                cwd=self.project,
                env=environment,
                input=json.dumps(payload | event),
                text=True,
                capture_output=True,
                check=False,
                timeout=30,
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "")

    def check(self, expected=0):
        result = self.command("check", "--format", "json", expected=expected)
        report = json.loads(result.stdout)
        self.assertIn(f"maida view {report['run_id']}", result.stderr)
        return report

    def test_capture_review_pass_fail_and_repair(self):
        self.command("init", approval="y")
        self.capture("known-good-session")
        known_good = self.check()["run_id"]
        self.command("init", "--from-run", known_good)
        review = json.loads((self.project / ".maida/starter/review.json").read_text())
        self.assertTrue(review["review_required"])
        self.assertFalse((self.project / ".maida/policy.yaml").exists())
        starter = self.project / ".maida/starter/policy.yaml"
        candidate = yaml.safe_load(starter.read_text())
        candidate["metrics"]["required_tools"] = {
            "kind": "invariant",
            "all_of": ["Read"],
        }
        starter.write_text(yaml.safe_dump(candidate))
        self.command(
            "init", "--reviewed", "--reason", "This task must read its configuration"
        )
        policy = self.project / ".maida/policy.yaml"
        baseline = self.project / ".maida/baselines/agent.json"
        original_baseline = baseline.read_bytes()

        def gate(run_id, expected):
            result = self.command(
                "assert",
                run_id,
                "--baseline",
                str(baseline),
                "--policy",
                str(policy),
                "--format",
                "json",
                expected=expected,
            )
            return json.loads(result.stdout)

        self.assertTrue(gate(known_good, 0)["passed"])
        self.capture("broken-session", failing=True)
        failing = gate(self.check()["run_id"], 1)
        self.assertFalse(failing["passed"])
        self.assertIn("required_tools", json.dumps(failing))
        self.capture("repaired-session")
        self.assertTrue(gate(self.check()["run_id"], 0)["passed"])
        self.assertEqual(baseline.read_bytes(), original_baseline)
        self.assertFalse((self.project / "home/.maida").exists())

    def test_init_rejects_mixed_and_duplicate_observations(self):
        self.command("init", approval="y")
        self.capture("one-session")
        one = self.check()["run_id"]
        self.capture("another-session")
        another = self.check()["run_id"]
        mixed = self.command(
            "init", "--from-run", one, "--from-run", another, expected=2
        )
        self.assertIn("same workflow", mixed.stderr)
        duplicate = self.command(
            "init", "--from-run", one, "--from-run", one, expected=2
        )
        self.assertIn("duplicate runs", duplicate.stderr)
        self.assertFalse((self.project / ".maida/policy.yaml").exists())

    def test_empty_evidence_does_not_look_like_activation(self):
        result = self.command("init", "--from-run", "latest", expected=2)
        self.assertTrue(result.stderr.strip())
        self.assertFalse((self.project / ".maida/policy.yaml").exists())
        self.assertFalse((self.project / ".maida/starter").exists())

    def test_preview_approval_and_detach_preserve_local_state(self):
        before = self.settings.read_bytes()
        self.command("init", expected=2)
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertFalse((self.project / ".maida/local.json").exists())
        self.command("init", approval="n")
        self.assertEqual(self.settings.read_bytes(), before)
        self.command("init", approval="y")
        installed = self.settings.read_bytes()
        self.command("init")
        self.assertEqual(self.settings.read_bytes(), installed)
        self.capture("saved-session")
        saved = self.check()["run_id"]
        self.command("detach", "--agent", "claude-code", approval="y")
        self.assertEqual(json.loads(self.settings.read_text()), self.original_settings)
        self.command("check", expected=2)
        self.command("export", saved, "--out", str(self.project / "saved.json"))
        self.command("init", "--agent", "claude-code", approval="y")
        self.assertEqual(self.check()["run_id"], saved)
        self.assertFalse((self.project / ".maida/policy.yaml").exists())

    def test_check_rejects_missing_and_unfinished_capture_instead_of_sdk(self):
        self.command("init", approval="y")
        self.command("demo")
        missing = self.command("check", expected=2)
        self.assertIn("new Claude Code session", missing.stderr)
        self.capture("finished-session")
        captured = self.check()["run_id"]
        self.command("demo")
        self.assertEqual(self.check()["run_id"], captured)
        self.command(
            "capture",
            "claude-hook",
            payload={
                "session_id": "unfinished",
                "cwd": str(self.project),
                "hook_event_name": "SessionStart",
                "source": "startup",
            },
        )
        unfinished = self.command("check", expected=2)
        self.assertIn("Finish and exit", unfinished.stderr)

    def test_check_reports_loops_and_preserves_recovered_failures(self):
        self.command("init", approval="y")
        self.capture("recovered-session", recovered=True)
        recovered = self.check()["run_id"]
        output = self.project / "recovered.json"
        self.command("export", recovered, "--out", str(output))
        run = json.loads(output.read_text())["run"]
        self.assertEqual(run["status"], "ok")
        self.assertEqual(run["counts"]["errors"], 1)
        self.capture("looping-session", looping=True)
        self.assertFalse(self.check(expected=1)["passed"])


if __name__ == "__main__":
    unittest.main()
