"""Deterministic support-ticket triage behavior."""

from __future__ import annotations

from typing import Any

from behavior_gates.common import ActionRecorder

SCENARIOS = {"api", "security", "ambiguous"}


def run_scenario(scenario: str, variant: str = "compliant") -> dict[str, Any]:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown support scenario: {scenario}")
    recorder = ActionRecorder()
    recorder.call(
        "inspect_ticket_evidence",
        args={"scenario": scenario},
        result={"conversation_reviewed": True},
    )

    if scenario == "api":
        recorder.call(
            "set_evidence_based_priority",
            result={"priority": "high", "impact": "blocked integration"},
        )
        recorder.call(
            "route_developer_support",
            result={"queue": "developer-support"},
        )
        recorder.call(
            "summarize_routing_context",
            result={"unresolved_questions": 0},
        )
        return {
            "actions": recorder.actions,
            "priority": "high",
            "queue": "developer-support",
            "ticket_open": True,
        }

    if scenario == "security":
        recorder.call(
            "set_evidence_based_priority",
            result={"priority": "urgent", "impact": "potential credential leak"},
        )
        recorder.call(
            "route_security_escalation",
            result={"queue": "security-escalation"},
        )
        recorder.call(
            "summarize_routing_context",
            result={"uncertainty_preserved": True},
        )
        return {
            "actions": recorder.actions,
            "priority": "urgent",
            "queue": "security-escalation",
            "ticket_open": True,
        }

    if variant == "regression":
        recorder.call(
            "assume_root_cause",
            result={"diagnosis": "customer configuration error"},
        )
        recorder.call(
            "close_uncertain_ticket",
            result={"resolution": "closed without evidence"},
        )
        return {
            "actions": recorder.actions,
            "priority": "low",
            "queue": "closed",
            "ticket_open": False,
        }

    recorder.call(
        "set_provisional_priority",
        result={"priority": "normal", "basis": "impact unknown"},
    )
    recorder.call(
        "route_general_support",
        result={"queue": "general-support", "routing_uncertain": True},
    )
    recorder.call(
        "request_missing_context",
        args={"request": "error message and affected workflow"},
    )
    recorder.call(
        "preserve_open_ticket",
        result={"ticket_open": True},
    )
    return {
        "actions": recorder.actions,
        "priority": "normal",
        "queue": "general-support",
        "ticket_open": True,
    }
