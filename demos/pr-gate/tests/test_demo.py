"""End-to-end verification of the stage-safe Maida gate."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

import demo
import pytest


PROJECT_ROOT = Path(__file__).parents[1]


def test_safe_agent_matches_checked_in_baseline() -> None:
    with (
        tempfile.TemporaryDirectory(prefix="pr-gate-safe-test-") as checkout,
        tempfile.TemporaryDirectory(prefix="pr-gate-safe-traces-") as traces,
    ):
        temp_root = Path(checkout)
        demo._copy_demo(temp_root)
        demo._initialize_temp_repository(temp_root)
        env = os.environ.copy()
        env["MAIDA_DATA_DIR"] = traces

        completed = subprocess.run(
            [
                demo._maida_executable(),
                "run",
                "coding_agent.py",
                "--baseline",
                ".maida/baselines/coding-agent.json",
                "--policy",
                ".maida/policy.yaml",
                "--format",
                "markdown",
            ],
            cwd=temp_root / "pr-gate",
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )

    assert completed.returncode == 0, completed.stderr
    assert "Maida verdict: pass" in completed.stdout
    assert "Allowed tools stayed within the allowed range." in completed.stdout


def test_candidate_is_blocked_for_rewriting_regression_test() -> None:
    completed = subprocess.run(
        [sys.executable, "demo.py", "--gate-only", "--no-color"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Maida verdict: fail" in completed.stdout
    assert "Allowed tools violated the policy." in completed.stdout
    assert "New tool used: `rewrite_regression_test`" in completed.stdout
    assert "PR BLOCKED" in completed.stdout


def test_default_demo_shows_happy_and_regression_paths() -> None:
    completed = subprocess.run(
        [sys.executable, "demo.py", "--no-color"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "PATH 1 — Happy path with the original AGENTS.md" in completed.stdout
    assert "Impact check: VIP shipping remains $0.00." in completed.stdout
    assert "Maida verdict: pass" in completed.stdout
    assert "HAPPY PATH" in completed.stdout
    assert "PATH 2 — Same task after the AGENTS.md change" in completed.stdout
    assert "green suite now approves a $15.00 shipping charge" in completed.stdout
    assert "Maida verdict: fail" in completed.stdout
    assert "New tool used: `rewrite_regression_test`" in completed.stdout
    assert "PR BLOCKED" in completed.stdout


@pytest.mark.parametrize("tool_name", ["rewrite_regression_test", "unlisted_tool"])
def test_committed_regression_is_blocked_from_repository_root(tmp_path, tool_name):
    """Exercise the nested script path and real instructions used by the Action."""
    import shutil

    demo._copy_demo(tmp_path)
    shutil.copy2(PROJECT_ROOT / "AGENTS.md", tmp_path / "pr-gate/AGENTS.md")
    agent = tmp_path / "pr-gate/coding_agent.py"
    agent.write_text(
        agent.read_text().replace('"rewrite_regression_test"', repr(tool_name))
    )
    demo._initialize_temp_repository(tmp_path)
    completed = subprocess.run(
        [
            demo._maida_executable(),
            "run",
            "pr-gate/coding_agent.py",
            "--baseline",
            "pr-gate/.maida/baselines/coding-agent.json",
            "--policy",
            "pr-gate/.maida/policy.yaml",
            "--format",
            "json",
        ],
        cwd=tmp_path,
        env={**os.environ, "MAIDA_DATA_DIR": str(tmp_path / "traces")},
        capture_output=True,
        text=True,
        check=False,
    )
    assert completed.returncode == 1, completed.stdout + completed.stderr
    import json

    report = json.loads(completed.stdout)
    assert report["verdict"] == "fail"
    assert all(trial["process_exit_code"] == 0 for trial in report["trials"])
    assert any(
        trial["invariant_outcomes"]["no_new_tools"] is False
        for trial in report["trials"]
    )
    assert tool_name in completed.stdout


def test_workflow_uses_the_locked_engine_and_current_action():
    import json
    import re
    import tomllib
    import yaml

    lock = tomllib.loads((PROJECT_ROOT / "uv.lock").read_text())
    engine = next(
        package for package in lock["package"] if package["name"] == "maida-ai"
    )
    contract = json.loads(
        (PROJECT_ROOT.parents[1] / "tests/contracts/current-main.json").read_text()
    )
    workflow = yaml.safe_load(
        (PROJECT_ROOT.parents[1] / ".github/workflows/pr-gate.yml").read_text()
    )
    # The checked-in candidate deliberately fails. PR CI tests both outcomes;
    # publishing the failing Action check is an explicitly requested demo.
    assert workflow["jobs"]["maida"]["if"] == "github.event_name == 'workflow_dispatch'"
    step = next(
        step
        for step in workflow["jobs"]["maida"]["steps"]
        if "maida-assert@" in step.get("uses", "")
    )
    assert re.fullmatch(r"maida-ai/maida-assert@[0-9a-f]{40}", step["uses"])
    assert step["id"] == "maida"
    assert step["with"]["mode"] == "report-only"
    assert step["with"]["post-comment"] == "false"
    assert step["with"]["maida-version"] == contract["engine_ref"]
    assert engine["version"] == contract["engine_ref"].removeprefix("v")
    verdict_step = next(
        step
        for step in workflow["jobs"]["maida"]["steps"]
        if step.get("name") == "Fail on the expected Maida verdict"
    )
    assert verdict_step["env"]["VERDICT"] == "${{ steps.maida.outputs.verdict }}"
    assert 'if [ "$VERDICT" != "fail" ]; then' in verdict_step["run"]
    assert "exit 1" in verdict_step["run"]
