"""Execute the behavior matrix through the real Maida CLI."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from behavior_gates.matrix import GateCase

ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class GateResult:
    case: GateCase
    returncode: int
    report: dict[str, Any]
    stdout: str
    stderr: str

    @property
    def verdict(self) -> str:
        return str(self.report.get("verdict", "error"))

    @property
    def blocking_checks(self) -> tuple[str, ...]:
        checks = self.report.get("aggregate_results", [])
        return tuple(
            str(check["check_name"])
            for check in checks
            if check.get("mode") == "gating" and check.get("verdict") == "fail"
        )


def _maida_executable() -> str:
    adjacent = Path(sys.executable).with_name("maida")
    if adjacent.is_file():
        return str(adjacent)
    executable = shutil.which("maida")
    if executable is None:
        raise RuntimeError("maida executable not found; run this project with uv")
    return executable


def run_gate(
    case: GateCase,
    artifact_dir: Path,
    *,
    trials: int | None = None,
) -> GateResult:
    """Run one matrix case and return the persisted machine-readable report."""
    artifact_dir = artifact_dir.resolve()
    artifact_dir.mkdir(parents=True, exist_ok=True)
    report_path = artifact_dir / f"{case.name}.json"
    command = [
        _maida_executable(),
        "run",
        case.agent,
        "--policy",
        case.policy,
        "--format",
        "markdown",
        "--json-out",
        str(report_path),
    ]
    if trials is not None:
        command.extend(["--trials", str(trials)])

    environment = os.environ.copy()
    environment["MAIDA_DEMO_SCENARIO"] = case.scenario
    environment["MAIDA_DEMO_VARIANT"] = case.variant
    with tempfile.TemporaryDirectory(prefix=f"maida-{case.name}-") as data_dir:
        environment["MAIDA_DATA_DIR"] = data_dir
        completed = subprocess.run(
            command,
            cwd=ROOT,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )

    report: dict[str, Any] = {}
    if report_path.is_file():
        report = json.loads(report_path.read_text(encoding="utf-8"))
    return GateResult(
        case=case,
        returncode=completed.returncode,
        report=report,
        stdout=completed.stdout,
        stderr=completed.stderr,
    )


def run_gate_suite(
    cases: tuple[GateCase, ...],
    artifact_dir: Path,
    *,
    trials: int | None = None,
) -> tuple[GateResult, ...]:
    return tuple(run_gate(case, artifact_dir, trials=trials) for case in cases)


def write_suite_summary(results: tuple[GateResult, ...], artifact_dir: Path) -> Path:
    """Write a compact Markdown index for CI artifacts and local inspection."""
    lines = [
        "# Agent Behavior gate results",
        "",
        "| Case | Variant | Verdict | Blocking checks | Exit code |",
        "| --- | --- | --- | --- | ---: |",
    ]
    for result in results:
        blocking = ", ".join(result.blocking_checks) or "—"
        lines.append(
            f"| {result.case.name} | {result.case.variant} | "
            f"{result.verdict.upper()} | {blocking} | {result.returncode} |"
        )
    summary_path = artifact_dir.resolve() / "summary.md"
    summary_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary_path
