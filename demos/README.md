# Practice one failure at a time

Start with the [canonical coding-agent project](pr-gate/): one storefront, real application tests, and four agent changes. One command shows PASS, an innocuous instruction edit, then green tests hiding a $15 shipping defect that Maida fails. Try skipped verification and self-improvement using the same gate.

## Other focused lessons

- [Repeated test runs](coding_agent_refactor/): unchanged final answer, repeated work, then repair.
- [Repeated order lookup](broken_pr/): the smallest pass/fail loop for a tool-calling agent.
- [Imported traces](langfuse_import/): local fake API and idempotent read-only import.
- [Import walkthrough](langfuse-gate/): longer recording-friendly version with an explicitly separate live integration reference.
- [Behavior contracts](agent-behavior-gates/): advanced deterministic scenarios for support triage, research, and verification. Read the included third-party attribution before reuse.

Each independent lab has its own lockfile where needed. Run its documented `uv sync --locked` before its commands. The deterministic exercises use Maida 0.6.1 and must not be presented as evidence that a live agent or protected GitHub repository is gated.
