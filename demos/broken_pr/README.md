# Catch a broken agent change before merge

This deterministic order-status agent returns a plausible answer in both runs.
The regression is in its execution path: one order lookup becomes four identical
lookups. Maida catches that structural change even though the customer-facing
answer stays exactly the same.

The demo uses fixed local data. Running the agent makes no network calls and
needs no API keys, LLMs, or framework packages.

## What the gate checks

Two committed files define the expected behavior:

- [`.maida/baselines/broken-pr-demo.json`](../../.maida/baselines/broken-pr-demo.json)
  is the known-good structural signature: one `lookup_order` call followed by
  one `compose_reply` call, with no loop warnings.
- [`.maida/policy.yaml`](../../.maida/policy.yaml) allows no growth in steps,
  tool calls, or token cost; rejects loops, guardrails, new tools, and non-`ok`
  terminal status; and ignores ordinary local timing noise.

The workflow uses [`maida-ai/maida-assert@V4`](https://github.com/maida-ai/maida-assert)
with current Maida. The [Maida repository](https://github.com/maida-ai/maida)
and [regression-testing guide](https://github.com/maida-ai/maida/blob/main/docs/regression-testing.md)
cover the full baseline and policy workflow.

## Reproduce the passing check

From the repository root, install the locked environment, record the known-good
run, and assert the latest run directly. Maida defaults to the latest run, so no
run-ID extraction is needed.

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --locked
MAIDA_DATA_DIR=.maida/demo-runs uv run python demos/broken_pr/order_status_agent.py --lookups 1
MAIDA_DATA_DIR=.maida/demo-runs uv run maida assert \
  --baseline .maida/baselines/broken-pr-demo.json \
  --policy .maida/policy.yaml \
  --format markdown
```

The agent prints:

```text
Order ORD-1042 has shipped and will arrive Friday.
```

The gate exits with exit code `0`: two tool calls match the baseline, and no
loop is present.

## Reproduce the broken change

Now run the same agent with four lookups. The final answer is unchanged.

```bash
MAIDA_DATA_DIR=.maida/demo-runs uv run python demos/broken_pr/order_status_agent.py --lookups 4
MAIDA_DATA_DIR=.maida/demo-runs uv run maida assert \
  --baseline .maida/baselines/broken-pr-demo.json \
  --policy .maida/policy.yaml \
  --format markdown
```

The assertion exits with exit code `1`. Maida sees five total tool calls instead
of two, four repeated `lookup_order` calls instead of one, six structural steps
instead of two, and a loop warning.

## Locally reproduced report preview

The stable lines below were reproduced locally against current Maida—the same
source selected by `maida-version: '@main'` in the workflow. They preview the
report that the Action can render in CI, not a live pull request comment. The
released version in this repository's lock file reports the same regression but
may format its Markdown differently. Run-specific IDs and latency are omitted.

```markdown
## ❌ Maida verdict: fail

### Top behavior changes

| Behavior | Baseline | Current | Change |
|---|---|---|---|
| Steps | 2 | 6 | +200% |
| Loops/cycles | 0 | 1 | NEW |
| Tool calls | 2 | 5 | +150% |

**Tool changes:**
- 🔁 `lookup_order` — repeated 1 -> 4 calls
```

Fix the repeated work and rerun the passing commands. If a behavioral change is
intentional, inspect it before accepting a new baseline; do not update the
baseline merely to make the check green.
