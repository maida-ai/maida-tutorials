# Gate traces already captured in Langfuse

**Langfuse tells you what happened; Maida tells you whether it changed.** This
terminal demo imports existing Langfuse-shaped traces, captures known-good
behavior, proves an unchanged candidate passes, and blocks a support agent that
silently starts escalating the same ticket three times.

The fixture is synthetic and the API server is local. The importer, baseline,
comparison engine, policy checks, and Markdown verdict are production Maida
behavior.

## Run the offline demo

From `maida-tutorials/demos/langfuse-gate`:

```bash
uv sync --locked
uv run --frozen python demo.py
```

No Langfuse account, API key, LLM, or external service is required. After the
locked dependencies are installed, the demo makes no network request beyond a
loopback server bound to `127.0.0.1` on an ephemeral port.

The single command runs three acts:

1. **Known good:** import a support trace whose tool path is
   `lookup_account`, then capture it as the baseline.
2. **Safe candidate:** import a later trace with the same structure. Maida
   reports `PASS`.
3. **Regression:** import a trace whose final answer still looks fine but whose
   tool path is `escalate_case -> escalate_case -> escalate_case`. Maida finds
   a new tool, a loop, and step, tool-call, latency, and token growth, then ends
   with `PR BLOCKED`.

The expected Maida gate exit code `1` is treated as a successful demo outcome.
Runs and the generated baseline live in a temporary directory, so rehearsals
do not touch your real Maida store or leave repository artifacts.

For presenter-controlled pacing, use:

```bash
uv run --frozen python demo.py --recording
```

That is the same deterministic flow with a pause before each act. See the
[recording guide](RECORDING.md) for the short shot list.

## Try it with real Langfuse traces

The Langfuse importer is included in Maida 0.6.1. Install the released CLI, then provide the same credentials used by your Langfuse SDK:

```bash
uv tool install "maida-ai==0.6.1"

export LANGFUSE_PUBLIC_KEY=pk-lf-...
export LANGFUSE_SECRET_KEY=sk-lf-...
# Optional for a regional or self-hosted deployment:
export LANGFUSE_BASE_URL=https://us.cloud.langfuse.com
```

Import a known-good trace and save its baseline:

```bash
maida import langfuse --trace-id KNOWN_GOOD_TRACE_ID
maida baseline --out .maida/baselines/support-agent.json
```

Then import exactly one completed candidate trace and run the same focused
checks shown by the demo:

```bash
maida import langfuse --trace-id CANDIDATE_TRACE_ID
maida assert \
  --baseline .maida/baselines/support-agent.json \
  --no-new-tools \
  --no-loops \
  --cost-tolerance 0
```

`maida import langfuse` uses authenticated, read-only GET requests. It does not
modify Langfuse data, store credentials in the imported run, or upload the run
to a hosted Maida service. Input, output, metadata, and source details pass
through Maida's normal redaction and truncation boundary before local storage.

For CI, copy and adapt
[`examples/github-actions.yml`](examples/github-actions.yml). It keeps
credentials in GitHub secrets and uses the Action's trusted `trace-command`
mode to import exactly one trace per gate run. Do not build the trace command
from pull-request-controlled text or use a range that can create multiple runs.

The [full Langfuse import guide](https://maida.ai/langfuse/) covers selection,
mapping, self-hosted deployments, error handling, and privacy. The
[`maida-tutorials` walkthrough](https://github.com/maida-ai/maida-tutorials/tree/main/demos/langfuse_import)
is the longer copy-pasteable tutorial.

## What is synthetic and what is real

Synthetic and committed for repeatability:

- support-ticket observations and their timestamps, tokens, and durations;
- the loopback Langfuse-compatible endpoint;
- placeholder credentials used only between local child processes.

Production Maida behavior:

- authenticated `maida import langfuse` requests and normalization;
- local trace validation and storage;
- baseline capture and structural comparison;
- tool-path, loop, step, tool-call, latency, and token checks;
- the human-readable verdict and next steps.

## Development

```bash
uv sync --locked
uv run --frozen pytest -q
uv run --frozen python demo.py
uv run --frozen ruff check .
uv run --frozen ruff format --check .
```

The project lockfile pins the released Maida 0.6.1 engine for reproducible importer and gate behavior.

## Layout

```text
demo.py                     local API fixture and three-act presentation
observations.json           synthetic support-agent traces
.maida/policy.yaml          CI-ready policy v2 example
examples/github-actions.yml real Langfuse CI example
RECORDING.md                30–60 second recording runbook
tests/                      output, privacy, rerun, docs, and server tests
```
