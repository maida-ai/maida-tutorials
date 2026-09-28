"""Maida entrypoint for primary-source tax research scenarios."""

from behavior_gates.common import run_agent_entrypoint
from behavior_gates.tax import SCENARIOS, run_scenario

if __name__ == "__main__":
    raise SystemExit(
        run_agent_entrypoint(
            run_name="primary-source-tax-research",
            scenarios=SCENARIOS,
            default_scenario="direct-primary",
            runner=run_scenario,
        )
    )
