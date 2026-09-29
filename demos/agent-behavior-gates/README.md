# Agent Behavior gates with Maida

This demo turns four `BEHAVIOR.md` examples into deterministic, pre-merge Maida
gates. The behavior is exercised by small offline agents and checked from their
actual execution traces. There is no LLM judge, API key, network call, or
model-dependent verdict.

The source behavior documents are preserved under `.agents/behaviors/`. The
Python harnesses are an independent reimplementation designed to make compliant
and noncompliant action paths directly observable to Maida.

## Run the demo

```bash
uv sync --locked
uv run python demo.py --behavior all
```

Each behavior runs twice: a compliant path must pass, then a deliberately
regressed path must be blocked. A successful demonstration therefore includes
expected Maida `FAIL` verdicts. Reports are written to `.artifacts/demo/`.

Run one pair with `--behavior financial`, `support`, `tax`, or `cost`.

## Run the CI gate locally

```bash
uv run pytest -q
uv run ruff check .
uv run ruff format --check .
uv run python run_ci_gates.py
```

`run_ci_gates.py` runs all ten compliant scenarios with the three trials
declared by each policy and writes a consolidated summary plus the individual
machine-readable reports under `.artifacts/ci/`. The test suite also proves that
all four deliberately regressed paths exit with Maida's gate-failure code.

## Behavior-to-policy matrix

| Behavior | Scenario | Policy contract |
| --- | --- | --- |
| Financial work verification | verified values | inspect and preserve sources, verify arithmetic, separate assumptions, present a verified result |
| Financial work verification | discrepancy | preserve provenance, flag the mismatch, request source review; forbid invented or unverified values |
| Financial work verification | incomplete data | preserve provenance, mark uncertainty, request clarification; forbid invented or unverified values |
| Support ticket triage | API failure | inspect evidence, set an evidence-based priority, route with context |
| Support ticket triage | security risk | inspect evidence, set urgent priority, follow the security escalation route |
| Support ticket triage | ambiguous request | use a provisional priority and fallback queue, request only missing context, keep the ticket open |
| Primary-source tax research | direct primary research | read the method, consult primary authority, base the conclusion on it, then answer |
| Primary-source tax research | secondary-source locator | permit secondary discovery while still requiring primary authority before the conclusion |
| Cost-sensitive actions | known material cost | inspect pricing, surface cost, offer an alternative, request confirmation, then execute |
| Cost-sensitive actions | uncertain cost | inspect available pricing, state uncertainty, offer an alternative, request confirmation, do not execute |

Every policy also requires a normal stop condition, no loop or guardrail event,
and a hard upper bound on tool calls. See [`policies/`](policies/) for the
policy-as-code contracts.

## What the trace proves

The current policies gate exact required and forbidden action names and tool-call
limits. Maida also persists the ordered `tool_call_sequence`, per-tool counts,
and redacted action arguments for inspection. Some natural-language clauses
need richer policy predicates before they can be enforced directly—for example,
"read the skill *before* searching" or "confirm *before* this paid action."
Those gaps and proposed engine additions are recorded in the repository-local
`_ai_report/agent-behavior-followup.md`.

## Provenance and license

These examples originated in Braintrust's
[`agentbehavior`](https://github.com/braintrustdata/agentbehavior/tree/1866cffb530c93412719b7d3e243612a11bedf97/examples)
project. The four behavior documents and tax-research skill were copied
verbatim at commit `1866cffb530c93412719b7d3e243612a11bedf97` and are
redistributed under Apache License 2.0. The full upstream license and detailed
attribution are retained in [`LICENSE.agentbehavior`](LICENSE.agentbehavior)
and [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). This demo is independent
and is not affiliated with or endorsed by Braintrust.
