"""Run every compliant behavior scenario as the CI policy gate."""

from pathlib import Path

from behavior_gates.gates import run_gate_suite, write_suite_summary
from behavior_gates.matrix import POSITIVE_CASES


def main() -> int:
    artifact_dir = Path(".artifacts/ci")
    results = run_gate_suite(POSITIVE_CASES, artifact_dir)
    summary = write_suite_summary(results, artifact_dir)
    print(summary.read_text(encoding="utf-8"), end="")

    failed = [
        result
        for result in results
        if result.returncode != 0 or result.verdict != "pass"
    ]
    for result in failed:
        print(f"\n--- {result.case.name} stderr ---\n{result.stderr}")
        print(f"\n--- {result.case.name} stdout ---\n{result.stdout}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
