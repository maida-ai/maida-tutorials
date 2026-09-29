"""Deterministic primary-source tax research behavior."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from behavior_gates.common import ActionRecorder

SCENARIOS = {"direct-primary", "secondary-then-primary"}
SKILL_PATH = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "tax-research"
    / "SKILL.md"
)


def run_scenario(scenario: str, variant: str = "compliant") -> dict[str, Any]:
    if scenario not in SCENARIOS:
        raise ValueError(f"unknown tax scenario: {scenario}")
    recorder = ActionRecorder()
    skill = SKILL_PATH.read_text(encoding="utf-8")
    recorder.call(
        "read_tax_research_skill",
        args={"path": ".agents/skills/tax-research/SKILL.md"},
        result={"characters": len(skill), "method": "primary-source verification"},
    )

    if scenario == "secondary-then-primary":
        recorder.call(
            "search_secondary_sources",
            args={"query": "deductibility rule locator"},
        )
        recorder.call(
            "open_secondary_source",
            result={"purpose": "locate controlling authority"},
        )
        if variant == "regression":
            recorder.call(
                "answer_tax_question",
                result={"authority": "secondary"},
            )
            return {"actions": recorder.actions, "authority": "secondary"}

    recorder.call(
        "open_primary_source",
        args={"source_type": "statute"},
        result={"relevant_rule_found": True},
    )
    recorder.call(
        "base_conclusion_on_primary_source",
        result={"authority": "primary"},
    )
    recorder.call(
        "answer_tax_question",
        result={"authority": "primary"},
    )
    return {"actions": recorder.actions, "authority": "primary"}
