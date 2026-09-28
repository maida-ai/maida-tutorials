"""Show a passing and blocked behavior path without an LLM or network call."""

from __future__ import annotations

import argparse
from pathlib import Path

from behavior_gates.gates import run_gate, write_suite_summary
from behavior_gates.matrix import POSITIVE_CASES, REGRESSION_CASES

BEHAVIOR_KEYS = {
    "financial": "financial-work-verification",
    "support": "support-ticket-triage",
    "tax": "primary-source-tax-research",
    "cost": "cost-sensitive-actions",
}
DEMO_POSITIVE_NAMES = {
    "financial": "financial-discrepancy",
    "support": "support-ambiguous",
    "tax": "tax-secondary-then-primary",
    "cost": "cost-known",
}


def _case_by_name(cases: tuple, name: str):
    return next(case for case in cases if case.name == name)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run deterministic Maida gates for Agent Behavior examples."
    )
    parser.add_argument(
        "--behavior",
        choices=[*BEHAVIOR_KEYS, "all"],
        default="all",
        help="behavior pair to demonstrate (default: all)",
    )
    args = parser.parse_args()
    selected = list(BEHAVIOR_KEYS) if args.behavior == "all" else [args.behavior]
    artifact_dir = Path(".artifacts/demo")
    results = []

    for key in selected:
        positive = _case_by_name(POSITIVE_CASES, DEMO_POSITIVE_NAMES[key])
        regression = next(
            case for case in REGRESSION_CASES if case.behavior == BEHAVIOR_KEYS[key]
        )
        print(f"Running {key}: compliant path should pass")
        results.append(run_gate(positive, artifact_dir))
        print(f"Running {key}: regression path should be blocked")
        results.append(run_gate(regression, artifact_dir))

    suite = tuple(results)
    summary = write_suite_summary(suite, artifact_dir)
    print()
    print(summary.read_text(encoding="utf-8"), end="")
    unexpected = [
        result
        for result in suite
        if (
            result.case.variant == "compliant"
            and (result.returncode != 0 or result.verdict != "pass")
        )
        or (
            result.case.variant == "regression"
            and (result.returncode != 1 or result.verdict != "fail")
        )
    ]
    return 1 if unexpected else 0


if __name__ == "__main__":
    raise SystemExit(main())
