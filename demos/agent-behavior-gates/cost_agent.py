"""Maida entrypoint for cost-sensitive action scenarios."""

from behavior_gates.common import run_agent_entrypoint
from behavior_gates.cost import SCENARIOS, run_scenario

if __name__ == "__main__":
    raise SystemExit(
        run_agent_entrypoint(
            run_name="cost-sensitive-actions",
            scenarios=SCENARIOS,
            default_scenario="known",
            runner=run_scenario,
        )
    )
