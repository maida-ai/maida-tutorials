# Optional integration notebooks

Start with the [coding-agent walkthrough](coding-agent.md). These notebooks are reference labs; none is a prerequisite for your first gate. Commands below run from the maida-tutorials root.


### 1. Stop a Runaway Agent (`Guardrails/`)

**File:** `Guardrails/Stop a Runaway Agent.ipynb` **Install:** `uv pip install maida-ai`

A minimal introduction using only the core Maida SDK with no framework dependencies. Builds a tiny local agent that loops on the same tool call and model call, then shows how to:

- Observe a `LOOP_WARNING` in the timeline without stopping the run
- Enable `stop_on_loop` to abort execution as soon as the pattern repeats
- Compare the two runs side by side in `maida view`

Good starting point if you want to understand guardrails before looking at framework integrations.

---

### 2. Debug a LangGraph Agent (`LangChain/`)

**File:** `LangChain/Mock LangGraph Agent.ipynb` **Install:** `uv pip install "maida-ai[langchain]"`

Builds a multi-node LangGraph graph (search → calculate → save) using `FakeListLLM` and deterministic `@tool` functions. Covers:

- Adding `LangChainCallbackHandler` to a LangGraph run
- Verifying the exact happy-path signature: four LLM calls, three tool calls, and `search → calculator → save_result`
- A looping agent that triggers `LOOP_WARNING`
- Using `stop_on_loop` to abort the graph with `LOOP_WARNING → ERROR → RUN_END(status=error)`
- Missing dependencies, inactive-run behavior, normalized events, and Maida's storage redaction/truncation

---

### 3. Debug an OpenAI Agents Workflow (`OpenAI/`)

**File:** `OpenAI/Mock OpenAI Agent.ipynb` **Install:** `uv pip install "maida-ai[openai]" openai-agents`

Uses the OpenAI Agents SDK tracing API (`generation_span`, `function_span`) with deterministic inputs to drive the same quarterly-sales workflow without hitting any real model endpoint. Covers:

- Registering the Maida OpenAI Agents tracing processor via `set_trace_processors`
- Verifying the exact happy-path signature: four LLM calls, three tool calls, and `search → calculator → save_result`
- A looping workflow that triggers `LOOP_WARNING`
- Using `stop_on_loop` to finish with `LOOP_WARNING → ERROR → RUN_END(status=error)`
- Missing dependencies, inactive-run behavior, normalized events, and Maida's storage redaction/truncation
- Using `PROCESSOR.abort_exception` polling as a compatibility fallback for the SDK version locked by the tutorial

---

### 4. Debug a CrewAI Workflow (`CrewAI/`)

**NOTE:** CrewAI support was dropped after v0.5.3 because crewai dependency conflicts block Python 3.14 and openai upgrades. The adapter code remains in-tree; the `[crewai]` extra does not. See the [CrewAI guide](https://maida.ai/docs/integrations/crewai/) for details and the v0.5.3 pin.

**File:** `CrewAI/Mock CrewAI Agent.ipynb` **Historical isolated install:** `uv pip install "maida-ai[crewai]==0.5.3"`

Use a separate virtual environment for this historical notebook. The root project now uses Maida 0.6.1 and does not supply the CrewAI extra.

Runs the same deterministic search → calculate → save workflow through CrewAI's public execution-hook API. Covers:

- Activating the Maida CrewAI execution hooks
- Verifying the exact happy-path signature: four LLM calls, three tool calls, and `search → calculator → save_result`
- Recording an incomplete tool call as an error-status `TOOL_CALL` and `RUN_END(status=error)` when the tool raises
- Using `stop_on_loop` to abort repeated work with `LOOP_WARNING → ERROR → RUN_END(status=error)`
- Keeping CrewAI state in a temporary directory and disabling its native telemetry
- Missing dependencies, inactive-run behavior, normalized events, and Maida's storage redaction/truncation

---

## Running the notebooks

```bash
# From the repo root — install Maida and Jupyter
uv sync --group notebooks

# For LangChain notebook
uv pip install "maida-ai[langchain]"

# For OpenAI Agents notebook
uv pip install "maida-ai[openai]" openai-agents

# For CrewAI notebook
uv pip install "maida-ai[crewai]==0.5.3"

# Start Jupyter
uv run --group notebooks jupyter notebook
```

Open the notebook of your choice and run all cells in order. After each run, start the viewer in a terminal:

```bash
maida view
```

Policy files require an explicit supported v2+ version (`version: 2` for these examples). Policy v1 and files without a version are unsupported.

The baseline-relative `no_new_tools` rule is available from Maida 0.6.0. The root lockfile and CI use Maida 0.6.1 for current lessons.
