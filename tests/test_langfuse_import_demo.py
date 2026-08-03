import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
DEMO_DIR = REPO_ROOT / "demos" / "langfuse_import"
DEMO_SCRIPT = DEMO_DIR / "demo.py"
DEMO_README = DEMO_DIR / "README.md"


class LangfuseImportDemoTests(unittest.TestCase):
    def demo_environment(self) -> dict[str, str]:
        return os.environ.copy()

    def test_offline_demo_proves_idempotence_pass_and_regression(self):
        with tempfile.TemporaryDirectory() as temporary_directory:
            temp = Path(temporary_directory)
            result = subprocess.run(
                [
                    sys.executable,
                    str(DEMO_SCRIPT),
                    "--data-dir",
                    str(temp / "maida-data"),
                    "--baseline",
                    str(temp / "baseline.json"),
                ],
                cwd=REPO_ROOT,
                env=self.demo_environment(),
                capture_output=True,
                text=True,
                check=False,
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("Good trace imported", result.stdout)
        self.assertIn("Duplicate import skipped", result.stdout)
        self.assertIn("Baseline assertion: PASS", result.stdout)
        self.assertIn("Regression assertion: FAIL (expected)", result.stdout)
        self.assertNotIn("pk-fixture", result.stdout + result.stderr)
        self.assertNotIn("sk-fixture", result.stdout + result.stderr)

    def test_default_demo_is_rerunnable_without_repository_artifacts(self):
        for _ in range(2):
            result = subprocess.run(
                [sys.executable, str(DEMO_SCRIPT)],
                cwd=REPO_ROOT,
                env=self.demo_environment(),
                capture_output=True,
                text=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

        self.assertFalse((DEMO_DIR / ".demo-runs").exists())
        self.assertFalse((DEMO_DIR / ".demo-baseline.json").exists())

    def test_readmes_document_the_offline_import_gate(self):
        readme = DEMO_README.read_text(encoding="utf-8")
        for expected in (
            "uv run python demos/langfuse_import/demo.py",
            "No Langfuse account",
            "no network beyond the loopback server",
            "maida import langfuse",
            "fixture-good-trace",
            "fixture-regression-trace",
            "exit code `0`",
            "exit code `1`",
        ):
            self.assertIn(expected, readme)

        root_readme = (REPO_ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("[Langfuse import demo](demos/langfuse_import/)", root_readme)


if __name__ == "__main__":
    unittest.main()
