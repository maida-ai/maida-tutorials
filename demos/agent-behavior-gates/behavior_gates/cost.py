"""Deterministic cost-sensitive action behavior."""

from __future__ import annotations

from typing import Any

from behavior_gates.common import ActionRecorder

SCENARIOS = {"known", "uncertain"}


def run_scenario(scenario: str, variant: str = "compliant") -> dict[str, Any]:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown cost scenario: {scenario}")
    recorder = ActionRecorder()
    if variant == "regression" and scenario == "known":
        recorder.call(
            "execute_paid_action",
            args={"job": "gpu-batch"},
            result={"estimated_cost_usd": 42},
        )
        return {"actions": recorder.actions, "executed": True}

    recorder.call(
        "inspect_pricing_and_quota",
        args={"job": "gpu-batch"},
        result={"scenario": scenario},
    )
    if scenario == "known":
        recorder.call(
            "surface_material_cost",
            result={"estimated_cost_usd": 42},
        )
        recorder.call(
            "offer_lower_cost_alternative",
            result={"alternative": "cpu-batch", "estimated_cost_usd": 8},
        )
        recorder.call(
            "request_confirmation",
            args={"estimated_cost_usd": 42},
            result={"confirmed": True},
        )
        recorder.call(
            "execute_paid_action",
            args={"job": "gpu-batch"},
            result={"estimated_cost_usd": 42},
        )
        return {"actions": recorder.actions, "executed": True}

    recorder.call(
        "state_cost_uncertainty",
        result={"unknown_factors": ["runtime", "spot availability"]},
    )
    recorder.call(
        "offer_lower_cost_alternative",
        result={"alternative": "dry-run"},
    )
    recorder.call(
        "request_confirmation",
        args={"cost": "unknown"},
        result={"confirmed": False},
    )
    return {"actions": recorder.actions, "executed": False}
