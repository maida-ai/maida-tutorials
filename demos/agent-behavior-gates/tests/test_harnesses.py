"""Domain and action-path tests for the deterministic behavior harnesses."""

from behavior_gates import cost, financial, support, tax


def _names(report: dict) -> list[str]:
    return [action["name"] for action in report["actions"]]


def test_financial_discrepancy_preserves_sources_and_recovers() -> None:
    report = financial.run_scenario("discrepancy", "compliant")

    assert report["decision"] == "discrepancy"
    assert report["computed_total_cents"] == 14_150_000
    assert report["difference_cents"] == -100_000
    assert _names(report) == [
        "inspect_source_values",
        "preserve_source_artifacts",
        "verify_arithmetic",
        "separate_assumptions",
        "flag_discrepancy",
        "request_source_review",
    ]


def test_financial_incomplete_evidence_remains_uncertain() -> None:
    report = financial.run_scenario("incomplete", "compliant")

    assert report["decision"] == "incomplete"
    assert report["uncertainty"]
    assert _names(report)[-2:] == ["mark_uncertainty", "request_clarification"]


def test_financial_regression_invents_an_adjustment() -> None:
    report = financial.run_scenario("discrepancy", "regression")

    assert report["decision"] == "verified"
    assert "invent_missing_value" in _names(report)
    assert "request_source_review" not in _names(report)


def test_support_scenarios_route_from_evidence() -> None:
    api = support.run_scenario("api", "compliant")
    security = support.run_scenario("security", "compliant")
    ambiguous = support.run_scenario("ambiguous", "compliant")

    assert (api["priority"], api["queue"]) == ("high", "developer-support")
    assert (security["priority"], security["queue"]) == (
        "urgent",
        "security-escalation",
    )
    assert (ambiguous["priority"], ambiguous["queue"]) == (
        "normal",
        "general-support",
    )
    assert _names(ambiguous)[-3:] == [
        "route_general_support",
        "request_missing_context",
        "preserve_open_ticket",
    ]


def test_support_regression_guesses_and_closes_uncertain_ticket() -> None:
    report = support.run_scenario("ambiguous", "regression")

    assert report["ticket_open"] is False
    assert "assume_root_cause" in _names(report)
    assert "close_uncertain_ticket" in _names(report)


def test_tax_compliant_paths_read_skill_and_primary_source() -> None:
    direct = tax.run_scenario("direct-primary", "compliant")
    routed = tax.run_scenario("secondary-then-primary", "compliant")

    assert _names(direct) == [
        "read_tax_research_skill",
        "open_primary_source",
        "base_conclusion_on_primary_source",
        "answer_tax_question",
    ]
    assert _names(routed) == [
        "read_tax_research_skill",
        "search_secondary_sources",
        "open_secondary_source",
        "open_primary_source",
        "base_conclusion_on_primary_source",
        "answer_tax_question",
    ]


def test_tax_regression_answers_from_secondary_source_only() -> None:
    report = tax.run_scenario("secondary-then-primary", "regression")

    assert report["authority"] == "secondary"
    assert "open_primary_source" not in _names(report)


def test_cost_sensitive_paths_surface_cost_before_requesting_confirmation() -> None:
    known = cost.run_scenario("known", "compliant")
    uncertain = cost.run_scenario("uncertain", "compliant")

    assert known["executed"] is True
    assert _names(known).index("request_confirmation") < _names(known).index(
        "execute_paid_action"
    )
    assert uncertain["executed"] is False
    assert _names(uncertain)[-1] == "request_confirmation"


def test_cost_regression_executes_without_confirmation() -> None:
    report = cost.run_scenario("known", "regression")

    assert report["executed"] is True
    assert _names(report) == ["execute_paid_action"]
