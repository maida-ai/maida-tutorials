"""Coverage and schema tests for the BEHAVIOR-to-policy matrix."""

from pathlib import Path

from maida.policy import load_policy

from behavior_gates.matrix import POSITIVE_CASES, REGRESSION_CASES

ROOT = Path(__file__).parents[1]


def test_positive_matrix_covers_all_four_behaviors() -> None:
    assert {case.behavior for case in POSITIVE_CASES} == {
        "cost-sensitive-actions",
        "financial-work-verification",
        "primary-source-tax-research",
        "support-ticket-triage",
    }


def test_every_matrix_policy_is_valid_v2_and_every_agent_exists() -> None:
    for case in (*POSITIVE_CASES, *REGRESSION_CASES):
        policy = load_policy(ROOT / case.policy)
        assert policy.source_format == "v2"
        assert policy.trials == 3
        assert (ROOT / case.agent).is_file()


def test_every_behavior_spec_is_present() -> None:
    behavior_root = ROOT / ".agents" / "behaviors"
    behavior_names = {path.parent.name for path in behavior_root.glob("*/BEHAVIOR.md")}

    assert behavior_names == {case.behavior for case in POSITIVE_CASES}


def test_matrix_case_names_and_policy_pairs_are_unique() -> None:
    keys = [(case.name, case.policy) for case in POSITIVE_CASES]
    assert len(keys) == len(set(keys))
