"""Migration completeness and public entry points from a standalone checkout."""

import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConsolidationTests(unittest.TestCase):
    def test_every_migrated_tracked_file_has_a_destination(self):
        inventory = json.loads((ROOT / "migration-inventory.json").read_text())
        self.assertEqual({item["repository"] for item in inventory}, {"Demos", "maida"})
        for item in inventory:
            with self.subTest(path=item["destination"]):
                self.assertTrue((ROOT / item["destination"]).is_file())
                self.assertEqual(len(item["source_commit"]), 40)
                self.assertEqual(len(item["source_sha256"]), 64)
                self.assertNotIn(".venv", Path(item["destination"]).parts)
                self.assertNotIn(".git", Path(item["destination"]).parts)

    def test_first_step_does_not_require_a_checkout_or_notebook(self):
        readme = (ROOT / "README.md").read_text()
        first_command = readme.split("```bash", 1)[1].split("```", 1)[0]
        self.assertIn("maida demo --regression", first_command)
        self.assertNotIn("git clone", first_command)
        self.assertNotIn("jupyter", first_command)
        self.assertIn("guides/coding-agent.md", readme)
        self.assertIn("guides/python-agent.md", readme)

    def test_example_catalog_explains_external_service_boundaries(self):
        catalog = (ROOT / "examples/README.md").read_text()
        self.assertIn("minimal/simple_agent.py", catalog)
        self.assertIn("API keys", catalog)
        self.assertIn("historical", catalog)
        self.assertIn("uv sync", catalog)


if __name__ == "__main__":
    unittest.main()
