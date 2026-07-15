import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
AGENT_SCRIPT = REPO_ROOT / "demos" / "broken_pr" / "order_status_agent.py"
MAIDA_BIN = Path(sys.executable).with_name("maida")
EXPECTED_REPLY = "Order ORD-1042 has shipped and will arrive Friday."
BASELINE_PATH = REPO_ROOT / ".maida" / "baselines" / "broken-pr-demo.json"
POLICY_PATH = REPO_ROOT / ".maida" / "policy.yaml"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "maida.yml"
DEMO_README_PATH = REPO_ROOT / "demos" / "broken_pr" / "README.md"


class BrokenPrDemoTests(unittest.TestCase):
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

    def test_default_run_records_one_lookup_and_one_reply(self):
        result, data_dir, environment = self.run_agent("--lookups", "1")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), EXPECTED_REPLY)
        exported = self.export_latest_run(data_dir, environment)
        self.assertEqual(exported["run"]["run_name"], "broken-pr-order-status")
        self.assertEqual(exported["run"]["status"], "ok")
        self.assertGreater(exported["run"]["duration_ms"], 0)
        self.assertEqual(exported["run"]["counts"]["loop_warnings"], 0)
        self.assertEqual(
            [
                event["name"]
                for event in exported["events"]
                if event["event_type"] == "TOOL_CALL"
            ],
            ["lookup_order", "compose_reply"],
        )

    def test_repeated_lookups_preserve_reply_and_emit_loop_warning(self):
        result, data_dir, environment = self.run_agent("--lookups", "4")

        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), EXPECTED_REPLY)
        exported = self.export_latest_run(data_dir, environment)
        self.assertEqual(exported["run"]["status"], "ok")
        self.assertEqual(exported["run"]["counts"]["tool_calls"], 5)
        self.assertGreaterEqual(exported["run"]["counts"]["loop_warnings"], 1)
        self.assertIn(
            "LOOP_WARNING", [event["event_type"] for event in exported["events"]]
        )

    def test_lookup_count_must_be_positive(self):
        result, data_dir, _environment = self.run_agent("--lookups", "0")

        self.assertEqual(result.returncode, 2)
        self.assertIn("--lookups must be at least 1", result.stderr)
        self.assertFalse(data_dir.exists())

    def test_committed_baseline_describes_the_passing_trace(self):
        baseline = json.loads(BASELINE_PATH.read_text(encoding="utf-8"))

        self.assertEqual(baseline["source_run_name"], "broken-pr-order-status")
        self.assertEqual(baseline["summary"]["status"], "ok")
        self.assertEqual(baseline["summary"]["tool_calls"], 2)
        self.assertEqual(baseline["summary"]["loop_warnings"], 0)
        self.assertGreater(baseline["summary"]["duration_ms"], 0)
        self.assertEqual(
            baseline["tool_call_counts"], {"lookup_order": 1, "compose_reply": 1}
        )
        self.assertEqual(baseline["tool_path"], ["compose_reply", "lookup_order"])

    def test_policy_and_workflow_pin_the_demo_gate_contract(self):
        policy = POLICY_PATH.read_text(encoding="utf-8")
        for expected in (
            "step_tolerance: 0",
            "tool_call_tolerance: 0",
            "cost_tolerance: 0",
            "duration_tolerance: 1000",
            "no_loops: true",
            "no_guardrails: true",
            "no_new_tools: true",
            "expect_status: ok",
        ):
            self.assertIn(expected, policy)

        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        for expected in (
            "actions/checkout@v7",
            "maida-ai/maida-assert@V4",
            "agent-script: demos/broken_pr/order_status_agent.py",
            "baseline: .maida/baselines/broken-pr-demo.json",
            "policy: .maida/policy.yaml",
            "maida-version: '@main'",
        ):
            self.assertIn(expected, workflow)

        ignore_rules = (REPO_ROOT / ".gitignore").read_text(encoding="utf-8")
        self.assertIn(".maida/demo-runs/", ignore_rules)
        self.assertIn("!.maida/baselines/broken-pr-demo.json", ignore_rules)

    def test_passing_trace_satisfies_the_committed_gate(self):
        result, _data_dir, environment = self.run_agent("--lookups", "1")
        self.assertEqual(result.returncode, 0, result.stderr)

        assertion = self.run_gate(environment)
        self.assertEqual(assertion.returncode, 0, assertion.stdout + assertion.stderr)
        self.assertIn("no behavioral regression", assertion.stdout)

    def test_repeated_trace_fails_the_committed_gate(self):
        result, _data_dir, environment = self.run_agent("--lookups", "4")
        self.assertEqual(result.returncode, 0, result.stderr)

        assertion = self.run_gate(environment)
        self.assertEqual(assertion.returncode, 1, assertion.stdout + assertion.stderr)
        self.assertIn("agent behavior regressed", assertion.stdout)
        self.assertIn("`tool_calls`", assertion.stdout)
        self.assertIn("`no_loops`", assertion.stdout)
        self.assertIn("5 tool calls (baseline: 2", assertion.stdout)

    def test_demo_readme_teaches_local_pass_and_failure_without_run_ids(self):
        readme = DEMO_README_PATH.read_text(encoding="utf-8")

        for expected in (
            "uv run python demos/broken_pr/order_status_agent.py --lookups 1",
            "uv run python demos/broken_pr/order_status_agent.py --lookups 4",
            "uv run maida assert",
            ".maida/baselines/broken-pr-demo.json",
            ".maida/policy.yaml",
            "exit code `0`",
            "exit code `1`",
            "## ❌ Maida verdict: fail",
            "| Tool calls | 2 | 5 | +150% |",
            "`lookup_order` — repeated 1 -> 4 calls",
            "not a live pull request comment",
            "https://github.com/maida-ai/maida",
            "https://github.com/maida-ai/maida/blob/main/docs/regression-testing.md",
        ):
            self.assertIn(expected, readme)

        self.assertNotIn("<TRACE_ID>", readme)
        self.assertNotIn("maida list |", readme)

    def test_root_readme_links_to_the_broken_pr_demo(self):
        readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn("[Broken PR demo](demos/broken_pr/)", readme)


if __name__ == "__main__":
    unittest.main()
