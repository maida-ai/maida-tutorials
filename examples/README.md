# Runnable examples

These examples moved from the Maida engine into the tutorial repository. Start with the [released onboarding route](https://maida.ai/docs/getting-started/); come here when you need a small integration to adapt.

From the maida-tutorials root:

```bash
uv sync --locked
MAIDA_DATA_DIR=.maida/onboarding-runs uv run python examples/minimal/simple_agent.py
MAIDA_DATA_DIR=.maida/onboarding-runs uv run maida list
```

The first example makes no network calls and creates one local run with a tool call and a model event. The event is simulated; no model is invoked. Set `MAIDA_DATA_DIR` for subsequent commands too so the viewer and CLI read the same storage.

- [minimal/simple_agent.py](minimal/simple_agent.py): one function and two recorders; no framework.
- [demo/pure_python.py](demo/pure_python.py): local tool error, loop, redaction, and timeline events.
- [demo/guardrails.py](demo/guardrails.py): observe a loop, then stop it explicitly.
- [langchain/minimal.py](langchain/minimal.py): deterministic adapter example; run `uv sync --locked --extra langchain`, then `uv run --extra langchain python examples/langchain/minimal.py`.
- [openai_agents/minimal.py](openai_agents/minimal.py): offline tracing API example; use `uv sync --locked --extra openai`, then `uv run --extra openai python examples/openai_agents/minimal.py`.
- [crewai/minimal.py](crewai/minimal.py): historical adapter example. Support ended after v0.5.3; use an isolated `maida-ai[crewai]==0.5.3` environment, not the current root extras.
- [langchain/customer_support.py](langchain/customer_support.py): advanced imported example requiring API keys, external services, and a downloaded database. Follow its [setup reference](langchain/_customer_support/README.md) only when you deliberately want the live integration. It is not an onboarding prerequisite or offline verification target.

The root project contains the example dependencies for supported offline integrations. Avoid running from nested legacy project directories, which describe the historical upstream example environment. An isolated `uv tool install` alone cannot satisfy `import maida` in your project interpreter.
