"""Pins in this repository must match the Python-owned Maida contract."""

import json
import tomllib
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = Path(__file__).parent / "contracts" / "current-main.json"
WORKFLOW_PATH = REPO_ROOT / ".github" / "workflows" / "maida.yml"


def read_contract() -> dict:
    return json.loads(CONTRACT_PATH.read_text(encoding="utf-8"))


class CrossRepoContractTests(unittest.TestCase):
    def test_engine_dependency_tracks_the_contract_channel(self):
        contract = read_contract()
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn(contract["install_requirement"], pyproject)

    def test_workflow_tracks_the_contract_action_and_engine(self):
        contract = read_contract()
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")
        pyproject = (REPO_ROOT / "pyproject.toml").read_text(encoding="utf-8")

        self.assertIn(f"uses: {contract['action_ref']}", workflow)
        self.assertNotIn("maida-ai = { git = ", pyproject)
        self.assertIn(f"maida-version: {contract['engine_ref']}", workflow)
        lock = (REPO_ROOT / "uv.lock").read_text()
        engine = next(
            block
            for block in lock.split("[[package]]")
            if '\nname = "maida-ai"\n' in block
        )
        self.assertIn(f'version = "{contract["engine_ref"].removeprefix("v")}"', engine)

    def test_workflow_does_not_pin_stale_uppercase_action_tags(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        for stale_ref in ("@V2", "@V3", "@V4", "@V5"):
            self.assertNotIn(f"maida-ai/maida-assert{stale_ref}", workflow)

    def test_runnable_projects_lock_the_released_engine(self):
        contract = read_contract()
        for project in (
            ".",
            "demos/pr-gate",
            "demos/langfuse-gate",
            "demos/agent-behavior-gates",
        ):
            with self.subTest(project=project):
                directory = REPO_ROOT / project
                config = tomllib.loads((directory / "pyproject.toml").read_text())
                self.assertIn(
                    contract["install_requirement"], config["project"]["dependencies"]
                )
                lock = tomllib.loads((directory / "uv.lock").read_text())
                engine = next(
                    package
                    for package in lock["package"]
                    if package["name"] == "maida-ai"
                )
                self.assertEqual(
                    engine["version"], contract["engine_ref"].removeprefix("v")
                )

    def test_published_onboarding_uses_the_contract_release(self):
        version = read_contract()["engine_ref"].removeprefix("v")
        for path in (
            ".github/workflows/tutorials.yml",
            "CONTRIBUTING.md",
            "guides/coding-agent.md",
        ):
            with self.subTest(path=path):
                self.assertIn(f"maida-ai=={version}", (REPO_ROOT / path).read_text())


if __name__ == "__main__":
    unittest.main()
