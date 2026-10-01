"""Acceptance cases for the checked-in policy, not inferred from its contents."""

import copy
import unittest
from pathlib import Path

from maida.gate import aggregate_metrics, invariant_outcomes, numeric_metrics
from maida.policy import load_policy
from maida.statistics import GateVerdict

POLICY = Path(__file__).resolve().parents[1] / ".maida/policy.yaml"
# This list is the reviewed contract. Do not derive it from the policy under test.
EXPECTED_CHECKS = {
    "forbidden_tools",
    "no_new_tools",
    "required_tools",
    "stop_condition_reached",
}
TOOLS = ["read_project_instructions", "run_regression_suite"]
CASES = [
    ("required_tools", None, "tool_path", ["read_project_instructions"]),
    ("no_new_tools", None, "tool_path", ["read_project_instructions", "unlisted_tool"]),
    (
        "forbidden_tools",
        None,
        "tool_path",
        ["read_project_instructions", "rewrite_regression_test"],
    ),
    ("stop_condition_reached", "summary", "status", "error"),
]


class CheckedInPolicyContractTests(unittest.TestCase):
    def test_every_protection_is_present_and_enforces_its_contract(self):
        policy = load_policy(POLICY)
        good = {
            "summary": {
                "status": "ok",
                "total_events": 4,
                "tool_calls": len(TOOLS),
                "total_tokens": 100,
                "duration_ms": 100,
                "loop_warnings": 0,
            },
            "tool_path": TOOLS,
            "guardrail_events": [],
        }
        baseline = copy.deepcopy(good)
        for failed_check, section, key, value in [(None, None, None, None), *CASES]:
            with self.subTest(check=failed_check):
                candidate = copy.deepcopy(good)
                if section:
                    candidate[section][key] = value
                elif key:
                    candidate[key] = value
                results = aggregate_metrics(
                    policy=policy,
                    trial_values=[numeric_metrics(candidate)],
                    trial_invariants=[invariant_outcomes(candidate, policy, baseline)],
                    process_outcomes=[True],
                    baseline=baseline,
                    trials_budgeted=1,
                    stopping_rule="fixed_n",
                )
                by_name = {
                    result.check_name: result
                    for result in results
                    if result.check_name != "agent_process"
                }
                self.assertEqual(
                    set(by_name),
                    EXPECTED_CHECKS,
                    "A policy protection was dropped or substituted",
                )
                for result in by_name.values():
                    self.assertEqual(result.mode, "gating")
                    self.assertIn(result.verdict, {GateVerdict.PASS, GateVerdict.FAIL})
                if failed_check:
                    # Overall FAIL alone is insufficient: another rule can hide
                    # the fact that this specific protection stopped working.
                    self.assertEqual(by_name[failed_check].verdict, GateVerdict.FAIL)
                else:
                    self.assertTrue(
                        all(
                            result.verdict is GateVerdict.PASS
                            for result in by_name.values()
                        )
                    )
