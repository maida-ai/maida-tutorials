from __future__ import annotations

import base64
import importlib.util
import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import pytest


DEMO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DEMO_DIR.parent
DEMO_SCRIPT = DEMO_DIR / "demo.py"


def run_demo(
    *arguments: str, input_text: str | None = None
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(DEMO_SCRIPT), *arguments],
        cwd=DEMO_DIR,
        env=os.environ.copy(),
        input=input_text,
        capture_output=True,
        text=True,
        check=False,
    )


def load_demo_module():
    assert DEMO_SCRIPT.exists(), "demo.py has not been implemented"
    spec = importlib.util.spec_from_file_location("langfuse_gate_demo", DEMO_SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_automatic_demo_proves_pass_then_blocks_escalation_loop():
    result = run_demo()

    assert result.returncode == 0, result.stdout + result.stderr
    combined = result.stdout + result.stderr
    expected_in_order = (
        "ACT 1 — Capture known-good behavior",
        "$ maida import langfuse --trace-id support-agent-baseline",
        "ACT 2 — Verify unchanged behavior",
        "Maida verdict: pass",
        "ACT 3 — Catch the regression",
        "Maida verdict: fail",
        "PR BLOCKED",
    )
    positions = [combined.index(text) for text in expected_in_order]
    assert positions == sorted(positions)
    for reason_code in (
        "new_tool_path",
        "loop_detected",
        "step_count_exceeded",
        "tool_call_count_exceeded",
        "cost_envelope_exceeded",
        "latency_envelope_exceeded",
    ):
        assert reason_code in combined
    assert "lookup_account" in combined
    assert "escalate_case -> escalate_case -> escalate_case" in combined
    assert "pk-fixture" not in combined
    assert "sk-fixture" not in combined
    assert "/tmp/" not in combined


def test_recording_mode_pauses_between_the_three_acts():
    result = run_demo("--recording", input_text="\n\n\n")

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.stdout.count("Press Enter") == 3
    assert "PR BLOCKED" in result.stdout


def test_default_demo_is_rerunnable_without_repository_artifacts():
    before = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout

    for _ in range(2):
        result = run_demo()
        assert result.returncode == 0, result.stdout + result.stderr

    after = subprocess.run(
        ["git", "status", "--short"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    assert after == before
    assert not (DEMO_DIR / ".demo-runs").exists()
    assert not (DEMO_DIR / ".demo-baseline.json").exists()


def test_fixture_server_requires_authentication_and_one_trace_id():
    demo = load_demo_module()
    credentials = base64.b64encode(b"pk-fixture:sk-fixture").decode("ascii")

    with demo.fixture_server() as base_url:
        with pytest.raises(urllib.error.HTTPError) as unauthenticated:
            urllib.request.urlopen(
                f"{base_url}/api/public/v2/observations?traceId=support-agent-baseline",
                timeout=2,
            )
        assert unauthenticated.value.code == 401

        request = urllib.request.Request(
            f"{base_url}/api/public/v2/observations",
            headers={"Authorization": f"Basic {credentials}"},
        )
        with pytest.raises(urllib.error.HTTPError) as missing_trace:
            urllib.request.urlopen(request, timeout=2)
        assert missing_trace.value.code == 400

        request = urllib.request.Request(
            f"{base_url}/api/public/v2/observations?traceId=support-agent-baseline",
            headers={"Authorization": f"Basic {credentials}"},
        )
        with urllib.request.urlopen(request, timeout=2) as response:
            payload = json.load(response)
        assert payload["data"]
        assert {row["traceId"] for row in payload["data"]} == {"support-agent-baseline"}
