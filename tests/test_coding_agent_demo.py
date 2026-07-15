import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_SCRIPT = (
    REPO_ROOT / "demos" / "coding_agent_refactor" / "refactoring_agent.py"
)
MAIDA_BIN = Path(sys.executable).with_name("maida")
EXPECTED_REPLY = "Refactor complete; 12 tests passed."
BASELINE_PATH = REPO_ROOT / ".maida" / "baselines" / "coding-agent-refactor.json"
POLICY_PATH = REPO_ROOT / ".maida" / "policy.yaml"
DEMO_README_PATH = REPO_ROOT / "demos" / "coding_agent_refactor" / "README.md"


class CodingAgentDemoTests(unittest.TestCase):
    def run_agent(self, *arguments: str):
        temporary_directory = tempfile.TemporaryDirectory()
        self.addCleanup(temporary_directory.cleanup)
        data_dir = Path(temporary_directory.name) / "maida-data"
        environment = os.environ.copy()
        environment["MAIDA_DATA_DIR"] = str(data_dir)

        result = subprocess.run(
            [sys.executable, str(AGENT_SCRIPT), *arguments],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        return result, data_dir, environment

    def export_latest_run(self, data_dir: Path, environment: dict[str, str]):
        export_path = data_dir.parent / "export.json"
        result = subprocess.run(
            [str(MAIDA_BIN), "export", "--out", str(export_path)],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(export_path.read_text(encoding="utf-8"))

    def run_gate(self, environment: dict[str, str]):
        return subprocess.run(
            [
                str(MAIDA_BIN),
                "assert",
                "--baseline",
                str(BASELINE_PATH),
                "--policy",
                str(POLICY_PATH),
                "--format",
                "markdown",
            ],
            cwd=REPO_ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    def test_good_refactor_records_inspect_edit_and_one_test(self):
        result, data_dir, environment = self.run_agent("--mode", "good")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), EXPECTED_REPLY)
        exported = self.export_latest_run(data_dir, environment)
        self.assertEqual(exported["run"]["run_name"], "coding-agent-refactor")
        self.assertEqual(exported["run"]["status"], "ok")
        self.assertGreater(exported["run"]["duration_ms"], 0)
        self.assertEqual(exported["run"]["counts"]["tool_calls"], 3)
        self.assertEqual(exported["run"]["counts"]["loop_warnings"], 0)
        self.assertEqual(
            [
                event["name"]
                for event in exported["events"]
                if event["event_type"] == "TOOL_CALL"
            ],
            ["inspect_repository", "edit_module", "run_tests"],
        )

    def test_regression_repeats_tests_but_preserves_the_final_answer(self):
        result, data_dir, environment = self.run_agent("--mode", "regression")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), EXPECTED_REPLY)
        exported = self.export_latest_run(data_dir, environment)
        self.assertEqual(exported["run"]["status"], "ok")
        self.assertEqual(exported["run"]["counts"]["tool_calls"], 5)
        self.assertGreaterEqual(exported["run"]["counts"]["loop_warnings"], 1)
        self.assertEqual(
            [
                event["name"]
                for event in exported["events"]
                if event["event_type"] == "TOOL_CALL"
            ],
            [
                "inspect_repository",
                "edit_module",
                "run_tests",
                "run_tests",
                "run_tests",
            ],
        )

    def test_mode_must_be_known(self):
        result, data_dir, _environment = self.run_agent("--mode", "unknown")

        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid choice", result.stderr)
        self.assertFalse(data_dir.exists())

    def test_committed_baseline_describes_the_good_refactor(self):
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(baseline["source_run_name"], "coding-agent-refactor")
        self.assertEqual(baseline["summary"]["status"], "ok")
        self.assertEqual(baseline["summary"]["tool_calls"], 3)
        self.assertEqual(baseline["summary"]["loop_warnings"], 0)
        self.assertGreater(baseline["summary"]["duration_ms"], 0)
        self.assertEqual(
            baseline["tool_call_counts"],
            {"inspect_repository": 1, "edit_module": 1, "run_tests": 1},
        )

    def test_good_refactor_passes_the_gate(self):
        result, _data_dir, environment = self.run_agent("--mode", "good")
        self.assertEqual(result.returncode, 0, result.stderr)

        assertion = self.run_gate(environment)
        self.assertEqual(assertion.returncode, 0, assertion.stdout + assertion.stderr)
        self.assertIn("no behavioral regression", assertion.stdout)

    def test_repeated_tests_fail_the_gate(self):
        result, _data_dir, environment = self.run_agent("--mode", "regression")
        self.assertEqual(result.returncode, 0, result.stderr)

        assertion = self.run_gate(environment)
        self.assertEqual(assertion.returncode, 1, assertion.stdout + assertion.stderr)
        self.assertIn("agent behavior regressed", assertion.stdout)
        self.assertIn("`tool_calls`", assertion.stdout)
        self.assertIn("`no_loops`", assertion.stdout)
        self.assertIn("5 tool calls (baseline: 3", assertion.stdout)

    def test_demo_readme_is_local_first_and_uses_latest_run_defaults(self):
        readme = DEMO_README_PATH.read_text(encoding="utf-8")

        for expected in (
            "--mode good",
            "--mode regression",
            "uv run maida assert",
            ".maida/baselines/coding-agent-refactor.json",
            ".maida/policy.yaml",
            "exit code `0`",
            "exit code `1`",
            "no API key",
            "no network",
            "https://github.com/maida-ai/skills/tree/main/product",
            "https://github.com/maida-ai/opencode-plugin",
        ):
            self.assertIn(expected, readme)

        self.assertNotIn("<TRACE_ID>", readme)
        self.assertNotIn("maida list |", readme)

    def test_root_readme_connects_the_skill_pack_and_demo(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        for expected in (
            "[coding-agent refactor demo](demos/coding_agent_refactor/)",
            "https://github.com/maida-ai/skills/tree/main/product",
            "`maida-instrument-agent`",
            "`maida-add-regression-gate`",
            "`maida-debug-gate`",
            "Codex, Claude Code, and OpenCode",
            "reviewable local diff",
            "does not push commits or upload traces",
            "https://github.com/maida-ai/opencode-plugin",
        ):
            self.assertIn(expected, readme)


if __name__ == "__main__":
    unittest.main()
