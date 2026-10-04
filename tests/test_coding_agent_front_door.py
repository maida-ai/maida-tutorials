"""The guide uses engine setup instead of the historical tutorial installer."""

import json
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]


class CodingAgentFrontDoorTests(unittest.TestCase):
    def test_first_report_precedes_baseline_review(self):
        text = (ROOT / "guides/coding-agent.md").read_text()
        version = json.loads((ROOT / "tests/contracts/current-main.json").read_text())["engine_ref"].removeprefix("v")
        block = text.split("```bash\n", 1)[1].split("```", 1)[0]
        self.assertIn(f'uv tool install "maida-ai=={version}"', block)
        self.assertIn("cd my-repo", block)
        self.assertLess(block.index("maida init"), block.index("maida check"))
        self.assertLess(block.index("maida check"), block.index('exact "View:" command'))
        self.assertIn("Claude Code task", block)
        self.assertIn("3 active checks passed", text)
        self.assertLess(text.index("maida view 83aa19e3"), text.index("## Protect the next agent change"))
        for example in re.findall(r"```bash\n(.*?)```", text, re.S):
            self.assertNotRegex(example, r"<[A-Z][A-Z_]*>")
        self.assertIn("$15", text)
        self.assertIn("VIP", text)
        self.assertEqual(set(re.findall(r"maida-ai==([\d.]+)", text)), {version})
        self.assertEqual(set(re.findall(r"Maida (?:v)?(\d+\.\d+\.\d+)", text)), {version})
        self.assertNotRegex(text, r"maida-ai/maida-assert@(?:V\d|v\d)")
        self.assertLess(text[: text.index("```bash")].count("\n"), 40)
        for obsolete in (
            "unreleased",
            "install_capture",
            "MAIDA_DATA_DIR",
            "capture claude-hook",
            "--expect-status",
            "--no-loops",
            "--no-guardrails",
            "@v5",
            "@V4",
        ):
            self.assertNotIn(obsolete, text)

    def test_run_id_examples_reach_maida_as_arguments(self):
        text = (ROOT / "guides/coding-agent.md").read_text()
        examples = [
            block
            for block in re.findall(r"```bash\n(.*?)```", text, re.S)
            if "--from-run" in block or "--baseline" in block
        ]
        self.assertEqual(len(examples), 2)
        for block in examples:
            with self.subTest(example=block):
                result = subprocess.run(
                    ["bash", "-eu", "-c", 'maida() { printf "%s\\n" "$@"; };\n' + block],
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                arguments = result.stdout.splitlines()
                if "--from-run" in block:
                    self.assertEqual(arguments, ["init", "--from-run", "paste-the-id-from-maida-check"])
                else:
                    self.assertEqual(arguments[:3], ["check", "assert", "paste-the-new-id-here"])
                    self.assertEqual(
                        arguments[3:], ["--baseline", ".maida/baselines/agent.json", "--policy", ".maida/policy.yaml"]
                    )
