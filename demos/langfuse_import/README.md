# Gate an existing Langfuse trace

This deterministic demo imports production-shaped synthetic observations from
a local fake Langfuse API, captures a known-good baseline, proves a matching
trace passes, then proves a structural regression fails. No Langfuse account,
API key, LLM, or framework package is required. It makes no network beyond the loopback server
started by the demo.

From the repository root:

```bash
uv sync --locked
uv run python demos/langfuse_import/demo.py
```

This tutorial repository currently pins Maida's `main` branch in `uv.lock` so
the importer is available before its next PyPI release.

The script exercises the real `maida import langfuse` CLI. It imports
`fixture-good-trace` twice to prove the operation is idempotent, saves a
temporary baseline, and checks the good trace with exit code `0`. It then
imports `fixture-regression-trace`, whose tool path changes from `lookup` to
three repeated `escalate` calls and whose token usage grows. The same assertion
returns exit code `1`, which the demo treats as the expected result.

The fixture is fully synthetic and committed next to the script. The fake API
binds to `127.0.0.1` on an ephemeral port; Maida still uses its normal
authenticated, read-only `/api/public/v2/observations` request path. Temporary
credentials exist only in the child-process environment and are never printed.
The default run and baseline storage are temporary, so rerunning the demo starts
from the same empty state and leaves the repository unchanged.

For a real Langfuse deployment, replace the local server with your Langfuse
base URL and set `LANGFUSE_PUBLIC_KEY` and `LANGFUSE_SECRET_KEY` in the
environment. See the [Langfuse import guide](https://github.com/maida-ai/maida/blob/main/docs/langfuse.md)
for selection, mapping, privacy, and CI guidance.
