"""Maida entrypoint for support-ticket triage scenarios."""

from behavior_gates.common import run_agent_entrypoint
from behavior_gates.support import SCENARIOS, run_scenario

if __name__ == "__main__":
    raise SystemExit(
        run_agent_entrypoint(
            run_name="support-ticket-triage",
            scenarios=SCENARIOS,
            default_scenario="api",
            runner=run_scenario,
        )
    )
