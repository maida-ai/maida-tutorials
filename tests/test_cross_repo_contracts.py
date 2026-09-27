"""Pins in this repository must match the Python-owned Maida contract."""

import json
import re
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

    def test_workflow_tracks_the_contract_action_and_locked_engine(self):
        contract = read_contract()
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        self.assertIn(f"uses: {contract['action_ref']}", workflow)
        # Unreleased policy support requires an immutable engine revision.
        # Check the installed lock and source declaration as well as CI; a
        # release literal alone previously allowed the project install to drift.
        pyproject = (REPO_ROOT / "pyproject.toml").read_text()
        revision = re.search(
            r'maida-ai = \{ git = "https://github.com/maida-ai/maida", rev = "([0-9a-f]{40})" \}',
            pyproject,
        )
        self.assertIsNotNone(revision)
        commit = revision.group(1)
        lock = (REPO_ROOT / "uv.lock").read_text()
        engine = next(
            block
            for block in lock.split("[[package]]")
            if '\nname = "maida-ai"\n' in block
        )
        self.assertIn(f"?rev={commit}#{commit}", engine)
        self.assertIn(f'maida-version: "@{commit}"', workflow)

    def test_workflow_does_not_pin_stale_uppercase_action_tags(self):
        workflow = WORKFLOW_PATH.read_text(encoding="utf-8")

        for stale_ref in ("@V2", "@V3", "@V4", "@V5"):
            self.assertNotIn(f"maida-ai/maida-assert{stale_ref}", workflow)


if __name__ == "__main__":
    unittest.main()
