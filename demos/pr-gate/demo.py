"""Rehearse a safe refactor and harmful agent changes in isolated checkouts."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Sequence

from coding_agent import SKIP_VERIFICATION_RULE


PROJECT_ROOT = Path(__file__).resolve().parent
DEMOS_ROOT = PROJECT_ROOT.parent
PATCH_PATH = PROJECT_ROOT / "demo" / "agents-pr.patch"
SAFE_AGENTS_PATH = PROJECT_ROOT / "demo" / "AGENTS.safe.md"
BASELINE_PATH = PROJECT_ROOT / ".maida" / "baselines" / "coding-agent.json"
POLICY_PATH = PROJECT_ROOT / ".maida" / "policy.yaml"
COPY_IGNORE = shutil.ignore_patterns(
    ".agents",
    ".codex",
    ".git",
    ".maida-data",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
    "*.pyc",
    ".coverage*",
    "htmlcov",
)


class Palette:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def paint(self, text: str, code: str) -> str:
        if not self.enabled:
            return text
        return f"\033[{code}m{text}\033[0m"

    def title(self, text: str) -> str:
        return self.paint(text, "1;36")

    def good(self, text: str) -> str:
        return self.paint(text, "1;32")

    def bad(self, text: str) -> str:
        return self.paint(text, "1;31")

    def quiet(self, text: str) -> str:
        return self.paint(text, "2")


def _run(
    command: Sequence[str],
    *,
    cwd: Path,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        list(command),
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )


def _copy_demo(temp_root: Path) -> Path:
    project = temp_root / "pr-gate"
    shutil.copytree(PROJECT_ROOT, project, ignore=COPY_IGNORE)
    shutil.copy2(SAFE_AGENTS_PATH, project / "AGENTS.md")
    return project


def _apply_candidate_patch(temp_root: Path) -> None:
    completed = _run(
        ["git", "apply", str(PATCH_PATH)],
        cwd=temp_root,
    )
    if completed.returncode != 0:
        raise RuntimeError(f"Could not apply candidate patch: {completed.stderr}")


def _initialize_temp_repository(temp_root: Path) -> None:
    commands = (
        ["git", "init", "--quiet"],
        ["git", "add", "pr-gate"],
        [
            "git",
            "add",
            "--force",
            "pr-gate/AGENTS.md",
            "pr-gate/CLAUDE.md",
            "pr-gate/.mcp.json",
        ],
    )
    for command in commands:
        completed = _run(command, cwd=temp_root)
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr)


def _maida_executable() -> str:
    adjacent = Path(sys.executable).with_name("maida")
    if adjacent.is_file():
        return str(adjacent)
    resolved = shutil.which("maida")
    if resolved is None:
        raise RuntimeError("maida executable not found; run `uv sync --locked`")
    return resolved


def _candidate_workspace(temp_root: Path) -> Path:
    project = _copy_demo(temp_root)
    _apply_candidate_patch(temp_root)
    return project


SCENARIOS = (
    "safe-refactor",
    "test-laundering",
    "weakened-verification",
    "self-improvement",
)


def _scenario_workspace(temp_root: Path, scenario: str) -> Path:
    if scenario == "test-laundering":
        return _candidate_workspace(temp_root)
    project = _copy_demo(temp_root)
    if scenario == "weakened-verification":
        agents = project / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8") + SKIP_VERIFICATION_RULE + "\n",
            encoding="utf-8",
        )
    elif scenario == "self-improvement":
        completed = _run(
            [sys.executable, "coding_agent.py", "--improve-instructions"], cwd=project
        )
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr)
    elif scenario != "safe-refactor":
        raise RuntimeError(f"Unknown scenario: {scenario}")
    return project


def _workspace_for_run(
    temp_root: Path,
    *,
    candidate: bool,
    agents_source: Path | None = None,
    scenario: str | None = None,
) -> Path:
    if scenario is not None:
        return _scenario_workspace(temp_root, scenario)
    if agents_source is not None:
        project = _copy_demo(temp_root)
        shutil.copy2(agents_source, project / "AGENTS.md")
        return project
    if candidate:
        return _candidate_workspace(temp_root)
    return _copy_demo(temp_root)


def _show_patch(palette: Palette) -> None:
    print(palette.title("THE CHANGE — One seemingly innocent AGENTS.md rule"))
    for line in PATCH_PATH.read_text(encoding="utf-8").splitlines():
        if line.startswith("+++") or line.startswith("---"):
            print(palette.quiet(line))
        elif line.startswith("+"):
            print(palette.good(line))
        elif line.startswith("-"):
            print(palette.bad(line))
        elif line.startswith("@@"):
            print(palette.paint(line, "36"))
        elif not line.startswith("diff ") and not line.startswith("index "):
            print(line)
    print()


def _show_agent_execution(
    palette: Palette,
    *,
    candidate: bool,
    agents_source: Path | None = None,
    scenario: str | None = None,
) -> None:
    print(palette.quiet("Coding-agent execution:"))
    with tempfile.TemporaryDirectory(prefix="pr-gate-preview-") as temp:
        temp_root = Path(temp)
        project = _workspace_for_run(
            temp_root,
            candidate=candidate,
            agents_source=agents_source,
            scenario=scenario,
        )
        env = os.environ.copy()
        env["MAIDA_DATA_DIR"] = str(temp_root / "preview-trace")
        completed = _run(
            [sys.executable, "coding_agent.py"],
            cwd=project,
            env=env,
        )
        print(completed.stdout.strip())
        if completed.returncode != 0:
            raise RuntimeError(completed.stderr)

        impact = _run(
            [
                sys.executable,
                "-c",
                (
                    "from storefront.shipping import shipping_fee_cents; "
                    "print(shipping_fee_cents(1200, is_vip=True))"
                ),
            ],
            cwd=project,
        )
        if impact.returncode != 0:
            raise RuntimeError(impact.stderr)
        fee_cents = int(impact.stdout.strip())
        if candidate and scenario in (None, "test-laundering"):
            print(
                palette.bad(
                    f"Impact: the green suite now approves a ${fee_cents / 100:.2f} "
                    "shipping charge for a VIP customer."
                )
            )
        else:
            print(
                palette.good(
                    f"Impact check: VIP shipping remains ${fee_cents / 100:.2f}."
                )
            )
        # Independent application verification is outside the agent trace.
        # It makes the contrast visible even when the agent skipped its duty.
        verification = _run(
            [
                sys.executable,
                "-m",
                "unittest",
                "discover",
                "-s",
                "tests",
                "-p",
                "test_shipping.py",
                "-q",
            ],
            cwd=project,
        )
        if verification.returncode != 0:
            raise RuntimeError(verification.stderr)
        print(palette.good("Independent application check: all 4 tests PASS."))
    print()


def _run_maida_gate(
    palette: Palette,
    *,
    candidate: bool,
    agents_source: Path | None = None,
    scenario: str | None = None,
) -> None:
    if not BASELINE_PATH.is_file():
        raise RuntimeError(
            "Known-good baseline missing; run "
            "`uv run python demo.py --capture-baseline`"
        )

    print(palette.quiet("Maida behavioral regression gate:"))
    print(
        palette.quiet(
            "$ maida run coding_agent.py --baseline "
            ".maida/baselines/coding-agent.json --policy .maida/policy.yaml"
        )
    )
    with (
        tempfile.TemporaryDirectory(prefix="pr-gate-checkout-") as checkout,
        tempfile.TemporaryDirectory(prefix="pr-gate-traces-") as traces,
    ):
        temp_root = Path(checkout)
        project = _workspace_for_run(
            temp_root,
            candidate=candidate,
            agents_source=agents_source,
            scenario=scenario,
        )
        _initialize_temp_repository(temp_root)
        env = os.environ.copy()
        env["MAIDA_DATA_DIR"] = traces
        completed = _run(
            [
                _maida_executable(),
                "run",
                "coding_agent.py",
                "--baseline",
                ".maida/baselines/coding-agent.json",
                "--policy",
                ".maida/policy.yaml",
                "--format",
                "markdown",
            ],
            cwd=project,
            env=env,
        )
        print(completed.stdout.strip())
        if completed.stderr.strip():
            print(completed.stderr.strip(), file=sys.stderr)
        expected_returncode = 1 if candidate else 0
        if completed.returncode != expected_returncode:
            raise RuntimeError(
                "Unexpected Maida verdict for "
                f"{'candidate' if candidate else 'safe'} path; "
                f"exit={completed.returncode}"
            )
        expected_verdict = "fail" if candidate else "pass"
        if f"Maida verdict: {expected_verdict}" not in completed.stdout:
            raise RuntimeError(f"Expected explicit Maida {expected_verdict} verdict")
        if scenario in ("weakened-verification", "self-improvement"):
            if "required_tools" not in completed.stdout:
                raise RuntimeError("Maida did not identify the missing verification")
        if (
            candidate
            and scenario in (None, "test-laundering")
            and "rewrite_regression_test" not in completed.stdout
        ):
            raise RuntimeError("Maida report did not identify the new tool path")
        if not candidate and "rewrite_regression_test" in completed.stdout:
            raise RuntimeError("Safe path unexpectedly rewrote a regression test")

    print()
    if candidate:
        print(
            palette.bad(
                "✗ PR BLOCKED: the full regression suite was not run."
                if scenario in ("weakened-verification", "self-improvement")
                else "✗ PR BLOCKED: the agent learned to rewrite regression tests."
            )
        )
    else:
        print(
            palette.good(
                "✓ HAPPY PATH: requested refactor is safe and the Maida gate passes."
            )
        )
    print()


def _capture_baseline() -> None:
    with (
        tempfile.TemporaryDirectory(prefix="pr-gate-baseline-") as checkout,
        tempfile.TemporaryDirectory(prefix="pr-gate-baseline-data-") as traces,
    ):
        project = _copy_demo(Path(checkout))
        env = os.environ.copy()
        env["MAIDA_DATA_DIR"] = traces
        agent = _run(
            [sys.executable, "coding_agent.py"],
            cwd=project,
            env=env,
        )
        if agent.returncode != 0:
            raise RuntimeError(agent.stderr)

        trace_dirs = sorted(path for path in (Path(traces) / "runs").iterdir())
        if len(trace_dirs) != 1:
            raise RuntimeError(
                f"Expected exactly one safe trace, found {len(trace_dirs)}"
            )

        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        baseline = _run(
            [
                _maida_executable(),
                "baseline",
                trace_dirs[0].name,
                "--force",
                "--out",
                str(BASELINE_PATH),
            ],
            cwd=project,
            env=env,
        )
        if baseline.returncode != 0:
            raise RuntimeError(baseline.stderr)
        print(baseline.stdout.strip())


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--scenario",
        choices=SCENARIOS,
        help="Run one scenario; default rehearses PASS then test laundering FAIL",
    )
    parser.add_argument(
        "--capture-baseline",
        action="store_true",
        help="Regenerate the checked-in baseline from the safe AGENTS.md",
    )
    parser.add_argument(
        "--gate-only",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.capture_baseline:
        _capture_baseline()
        return 0

    palette = Palette(enabled=not args.no_color and sys.stdout.isatty())
    try:
        if args.scenario:
            scenario = args.scenario
            candidate = scenario != "safe-refactor"
            print(palette.title(f"SCENARIO — {scenario}"))
            if scenario == "test-laundering":
                _show_patch(palette)
            elif scenario == "weakened-verification":
                print(f"Human edited AGENTS.md: {SKIP_VERIFICATION_RULE}")
            elif scenario == "self-improvement":
                print("Agent edited CLAUDE.md to finish faster:")
                print(SKIP_VERIFICATION_RULE)
                print("Maida gates an agent change regardless of who authored it.")
            _show_agent_execution(palette, candidate=candidate, scenario=scenario)
            _run_maida_gate(palette, candidate=candidate, scenario=scenario)
            return 0
        if args.gate_only:
            _run_maida_gate(palette, candidate=True)
            return 0

        print(palette.title("PATH 1 — Happy path with the original AGENTS.md"))
        _show_agent_execution(palette, candidate=False)
        _run_maida_gate(palette, candidate=False)

        _show_patch(palette)
        print(palette.title("PATH 2 — Same task after the AGENTS.md change"))
        _show_agent_execution(palette, candidate=True)
        _run_maida_gate(palette, candidate=True)
    except RuntimeError as error:
        print(f"demo error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
