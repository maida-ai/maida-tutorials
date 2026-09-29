"""Maida entrypoint for financial-work verification scenarios."""

from behavior_gates.common import run_agent_entrypoint
from behavior_gates.financial import SCENARIOS, run_scenario

if __name__ == "__main__":
    raise SystemExit(
        run_agent_entrypoint(
            run_name="financial-work-verification",
            scenarios=SCENARIOS,
            default_scenario="verified",
            runner=run_scenario,
        )
    )
