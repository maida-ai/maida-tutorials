"""Scenario-to-policy matrix used by tests, the demo, and CI."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class GateCase:
    name: str
    behavior: str
    scenario: str
    agent: str
    policy: str
    variant: str = "compliant"


POSITIVE_CASES = (
    GateCase(
        "financial-verified",
        "financial-work-verification",
        "verified",
        "financial_agent.py",
        "policies/financial-verified.yaml",
    ),
    GateCase(
        "financial-discrepancy",
        "financial-work-verification",
        "discrepancy",
        "financial_agent.py",
        "policies/financial-discrepancy.yaml",
    ),
    GateCase(
        "financial-incomplete",
        "financial-work-verification",
        "incomplete",
        "financial_agent.py",
        "policies/financial-incomplete.yaml",
    ),
    GateCase(
        "support-api",
        "support-ticket-triage",
        "api",
        "support_agent.py",
        "policies/support-api.yaml",
    ),
    GateCase(
        "support-security",
        "support-ticket-triage",
        "security",
        "support_agent.py",
        "policies/support-security.yaml",
    ),
    GateCase(
        "support-ambiguous",
        "support-ticket-triage",
        "ambiguous",
        "support_agent.py",
        "policies/support-ambiguous.yaml",
    ),
    GateCase(
        "tax-direct-primary",
        "primary-source-tax-research",
        "direct-primary",
        "tax_agent.py",
        "policies/tax-research.yaml",
    ),
    GateCase(
        "tax-secondary-then-primary",
        "primary-source-tax-research",
        "secondary-then-primary",
        "tax_agent.py",
        "policies/tax-research.yaml",
    ),
    GateCase(
        "cost-known",
        "cost-sensitive-actions",
        "known",
        "cost_agent.py",
        "policies/cost-known.yaml",
    ),
    GateCase(
        "cost-uncertain",
        "cost-sensitive-actions",
        "uncertain",
        "cost_agent.py",
        "policies/cost-uncertain.yaml",
    ),
)

REGRESSION_CASES = (
    GateCase(
        "financial-discrepancy-regression",
        "financial-work-verification",
        "discrepancy",
        "financial_agent.py",
        "policies/financial-discrepancy.yaml",
        "regression",
    ),
    GateCase(
        "support-ambiguous-regression",
        "support-ticket-triage",
        "ambiguous",
        "support_agent.py",
        "policies/support-ambiguous.yaml",
        "regression",
    ),
    GateCase(
        "tax-secondary-regression",
        "primary-source-tax-research",
        "secondary-then-primary",
        "tax_agent.py",
        "policies/tax-research.yaml",
        "regression",
    ),
    GateCase(
        "cost-known-regression",
        "cost-sensitive-actions",
        "known",
        "cost_agent.py",
        "policies/cost-known.yaml",
        "regression",
    ),
)
