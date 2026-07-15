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

    def test_default_run_records_one_lookup_and_one_reply(self):
        result, data_dir, environment = self.run_agent()

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


if __name__ == "__main__":
    unittest.main()
