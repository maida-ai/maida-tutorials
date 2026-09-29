"""Exercise relocated example entrypoints against isolated local trace storage."""

import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAIDA = Path(sys.executable).with_name("maida")


class ExampleTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.environment = os.environ.copy()
        self.environment.update(
            HOME=str(self.directory),
            MAIDA_DATA_DIR=str(self.directory / "data"),
            CREWAI_STORAGE_DIR=str(self.directory / "crewai"),
            CREWAI_DISABLE_TELEMETRY="true",
        )

    def run_example(self, path, *args):
        result = subprocess.run(
            [sys.executable, str(ROOT / path), *args],
            cwd=ROOT,
            env=self.environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        export = self.directory / "export.json"
        result = subprocess.run(
            [str(MAIDA), "export", "--out", str(export)],
            cwd=ROOT,
            env=self.environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return json.loads(export.read_text())

    def test_minimal_example_runs_without_a_sibling_engine_checkout(self):
        result = self.run_example("examples/minimal/simple_agent.py")
        self.assertEqual(result["run"]["status"], "ok")
        self.assertEqual(result["run"]["counts"]["tool_calls"], 1)
        self.assertEqual(result["run"]["counts"]["llm_calls"], 1)

    def verify_regression(self, path, tool):
        for args, expected in (((), 1), (("--regression",), 3)):
            exported = self.run_example(path, *args)
            calls = [
                event
                for event in exported["events"]
                if event["event_type"] == "TOOL_CALL" and event["name"] == tool
            ]
            self.assertEqual(len(calls), expected)
        invalid = subprocess.run(
            [sys.executable, str(ROOT / path), "--unknown-option"],
            env=self.environment,
            text=True,
            capture_output=True,
        )
        self.assertEqual(invalid.returncode, 2)

    @unittest.skipUnless(importlib.util.find_spec("agents"), "install the openai extra")
    def test_openai_example_records_success_and_regression_offline(self):
        self.verify_regression("examples/openai_agents/minimal.py", "lookup_docs")

    @unittest.skipUnless(
        importlib.util.find_spec("crewai"), "historical CrewAI environment is separate"
    )
    def test_historical_crewai_example_records_success_and_regression_offline(self):
        self.verify_regression("examples/crewai/minimal.py", "search_docs")

    @unittest.skipUnless(
        importlib.util.find_spec("langchain_core"), "install the langchain extra"
    )
    def test_langchain_example_records_a_real_callback(self):
        result = self.run_example("examples/langchain/minimal.py")
        self.assertEqual(result["run"]["counts"]["tool_calls"], 1)
        self.assertEqual(result["run"]["counts"]["llm_calls"], 1)


if __name__ == "__main__":
    unittest.main()
