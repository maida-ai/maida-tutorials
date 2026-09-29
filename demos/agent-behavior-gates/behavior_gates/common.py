"""Shared tracing and command-line helpers for the behavior harnesses."""

from __future__ import annotations

import json
import os
from collections.abc import Callable, Collection
from typing import Any

from maida import record_tool_call, traced_run


class ActionRecorder:
    """Record an action in both the test report and the active Maida trace."""

    def __init__(self) -> None:
        self.actions: list[dict[str, Any]] = []

    def call(
        self,
        name: str,
        *,
        args: dict[str, Any] | None = None,
        result: dict[str, Any] | None = None,
    ) -> None:
        action: dict[str, Any] = {"name": name}
        if args is not None:
            action["args"] = args
        if result is not None:
            action["result"] = result
        self.actions.append(action)
        record_tool_call(name, args=args, result=result)


ScenarioRunner = Callable[[str, str], dict[str, Any]]


def _environment_choice(name: str, allowed: Collection[str], default: str) -> str:
    value = os.environ.get(name, default)
    if value not in allowed:
        choices = ", ".join(sorted(allowed))
        raise ValueError(f"{name} must be one of: {choices}; got {value!r}")
    return value


def run_agent_entrypoint(
    *,
    run_name: str,
    scenarios: Collection[str],
    default_scenario: str,
    runner: ScenarioRunner,
) -> int:
    """Run one environment-selected scenario inside a persisted Maida trace."""
    scenario = _environment_choice("MAIDA_DEMO_SCENARIO", scenarios, default_scenario)
    variant = _environment_choice(
        "MAIDA_DEMO_VARIANT", {"compliant", "regression"}, "compliant"
    )
    with traced_run(name=run_name):
        report = runner(scenario, variant)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0
