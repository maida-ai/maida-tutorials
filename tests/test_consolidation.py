"""Migration completeness and public entry points from a standalone checkout."""

import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ConsolidationTests(unittest.TestCase):
    def test_star_request_follows_the_runnable_pass_to_fail_proof(self):
        readme = (ROOT / "README.md").read_text()
        requests = re.findall(r"(?m)^.*(?:⭐|\bstar\b).*$", readme)
        self.assertEqual(len(requests), 1)
        request = requests[0]
        self.assertIn("If this demo helped", request)
        self.assertIn("[star Maida](https://github.com/maida-ai/maida)", request)
        before = readme[: readme.index(request)].rstrip()
        proof = before.split("\n\n")[-1]
        for value in (
            "safe refactor",
            "PASS",
            "green application tests",
            "$15",
            "VIP",
            "Maida FAIL",
        ):
            self.assertIn(value, proof)
        self.assertLess(proof.index("PASS"), proof.index("Maida FAIL"))
        self.assertIn(
            "uv run --directory demos/pr-gate --frozen python demo.py", before
        )
        self.assertLess(
            readme.index(request), readme.index("## Try the standalone CLI")
        )

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

    def test_canonical_reference_is_the_first_runnable_project(self):
        readme = (ROOT / "README.md").read_text()
        first_command = readme.split("```bash", 1)[1].split("```", 1)[0]
        self.assertIn("uv sync --directory demos/pr-gate --locked", first_command)
        self.assertIn(
            "uv run --directory demos/pr-gate --frozen python demo.py", first_command
        )
        self.assertIn("maida demo --regression", readme)
        self.assertLess(
            readme.index("canonical coding-agent project"),
            readme.index("guides/coding-agent.md"),
        )
        self.assertNotIn("git clone", first_command)
        self.assertNotIn("jupyter", first_command)
        self.assertIn("guides/coding-agent.md", readme)
        self.assertIn("guides/python-agent.md", readme)

    def test_ci_verifies_each_canonical_scenario_offline(self):
        import yaml

        workflow = yaml.safe_load((ROOT / ".github/workflows/pr-gate.yml").read_text())
        job = workflow["jobs"]["scenarios"]
        self.assertEqual(
            set(job["strategy"]["matrix"]["scenario"]),
            {
                "safe-refactor",
                "test-laundering",
                "weakened-verification",
                "self-improvement",
            },
        )
        step = next(
            step
            for step in job["steps"]
            if step.get("name") == "Verify expected scenario verdict"
        )
        self.assertEqual(step["env"]["UV_OFFLINE"], "1")
        self.assertEqual(step["env"]["SCENARIO"], "${{ matrix.scenario }}")
        self.assertIn('demo.py --scenario "$SCENARIO"', step["run"])

    def test_example_catalog_explains_external_service_boundaries(self):
        catalog = (ROOT / "examples/README.md").read_text()
        self.assertIn("minimal/simple_agent.py", catalog)
        self.assertIn("API keys", catalog)
        self.assertIn("historical", catalog)
        self.assertIn("uv sync", catalog)


if __name__ == "__main__":
    unittest.main()
