"""Deterministic coding-agent refactor for the pre-merge gate demo."""

import argparse
import time

from maida import record_tool_call, trace


FINAL_REPLY = "Refactor complete; 12 tests passed."
TEST_RESULT = {
    "command": "uv run python -m unittest",
    "passed": 12,
    "failed": 0,
}


def inspect_repository() -> dict[str, object]:
    """Return a fixed repository summary without reading user files."""
    return {
        "language": "python",
        "test_command": TEST_RESULT["command"],
        "target": "src/order_service.py",
    }


def edit_module() -> dict[str, object]:
    """Simulate a small refactor without mutating the tutorial checkout."""
    return {
        "path": "src/order_service.py",
        "change": "extract validation helper",
        "files_changed": 1,
    }


def run_tests() -> dict[str, object]:
    """Return a deterministic local test result."""
    return TEST_RESULT.copy()


@trace(name="coding-agent-refactor")
def run_agent(mode: str = "good") -> str:
    """Perform the same refactor with either one or three test executions."""
    repository = inspect_repository()
    record_tool_call(
        "inspect_repository",
        args={"path": "."},
        result=repository,
    )

    change = edit_module()
    record_tool_call(
        "edit_module",
        args={"path": repository["target"]},
        result=change,
    )

    test_runs = 1 if mode == "good" else 3
    for _ in range(test_runs):
        result = run_tests()
        record_tool_call(
            "run_tests",
            args={"command": TEST_RESULT["command"]},
            result=result,
        )

    # Keep duration above zero on fast machines and released Maida builds.
    time.sleep(0.02)
    return FINAL_REPLY


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run the deterministic Maida coding-agent refactor demo."
    )
    parser.add_argument(
        "--mode",
        choices=("good", "regression"),
        default="good",
        help="run the efficient refactor or its repeated-test regression",
    )
    return parser.parse_args()


def main() -> None:
    arguments = parse_args()
    print(run_agent(mode=arguments.mode))


if __name__ == "__main__":
    main()
