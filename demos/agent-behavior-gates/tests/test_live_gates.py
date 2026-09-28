"""End-to-end tests through the real Maida runner and policy evaluator."""

from pathlib import Path

import pytest

from behavior_gates.gates import run_gate
from behavior_gates.matrix import POSITIVE_CASES, REGRESSION_CASES


@pytest.mark.parametrize("case", POSITIVE_CASES, ids=lambda case: case.name)
def test_compliant_scenario_passes_maida(case, tmp_path: Path) -> None:
    result = run_gate(case, tmp_path, trials=1)

    assert result.returncode == 0, result.stdout + result.stderr
    assert result.verdict == "pass"


@pytest.mark.parametrize("case", REGRESSION_CASES, ids=lambda case: case.name)
def test_regression_scenario_is_blocked_by_maida(case, tmp_path: Path) -> None:
    result = run_gate(case, tmp_path, trials=1)

    assert result.returncode == 1, result.stdout + result.stderr
    assert result.verdict == "fail"
    assert result.blocking_checks
