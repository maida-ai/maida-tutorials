# Practice one failure at a time

Start with the [released onboarding route](https://maida.ai/docs/getting-started/) and the [real-repository walkthrough](../guides/coding-agent.md). These labs deepen a specific lesson after your first report.

- [Shipping refactor](pr-gate/): real application tests, a deterministic coding harness, an instruction change, and a failed gate when the harness rewrites the test to hide a defect.
- [Repeated test runs](coding_agent_refactor/): unchanged final answer, repeated work, then repair.
- [Repeated order lookup](broken_pr/): the smallest pass/fail loop for a tool-calling agent.
- [Imported traces](langfuse_import/): local fake API and idempotent read-only import.
- [Import walkthrough](langfuse-gate/): longer recording-friendly version with an explicitly separate live integration reference.
- [Behavior contracts](agent-behavior-gates/): advanced deterministic scenarios for support triage, research, and verification. Read the included third-party attribution before reuse.
- [Injection arena archive](injection-arena/): preserved experiment with a custom classifier, not the Maida engine. It does not demonstrate Maida runtime prevention or a merge boundary. Live mode calls an external model; use canned mode for an offline replay.

Each independent lab has its own lockfile where needed. Run its documented `uv sync --locked` before its commands. Some labs intentionally pin development engine revisions; their capabilities must not be copied into released onboarding claims.
