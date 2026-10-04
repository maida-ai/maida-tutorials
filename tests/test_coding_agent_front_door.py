"""The guide uses engine setup instead of the historical tutorial installer."""

import json
from pathlib import Path
import re
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
        self.assertLess(block.index("maida check"), block.index("maida view <TRACE_ID>"))
        self.assertIn("Claude Code task", block)
        self.assertIn("3 active checks passed", text)
        self.assertLess(text.index("maida view <TRACE_ID>"), text.index("## Protect the next agent change"))
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
