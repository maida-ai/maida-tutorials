# Maida Tutorials

Interactive Jupyter notebooks for learning how to trace and debug AI agents with Maida.AI. All notebooks run without API keys or network calls. They use deterministic stubs and fake models.

## Start with a broken PR

The [Broken PR demo](demos/broken_pr/) is the shortest path from a known-good
agent run to a failing behavioral regression gate. It is deterministic, needs
no API key, and shows how an unchanged final answer can hide repeated tool work.

## Adopt Maida with a coding agent

The canonical [Maida coding-agent skill pack](https://github.com/maida-ai/skills/tree/main/product)
provides three explicit workflows for Codex, Claude Code, and OpenCode:

- `maida-instrument-agent` inspects the repository and adds the smallest fitting
  Maida integration.
- `maida-add-regression-gate` creates and reviews the baseline, policy, and CI
  gate.
- `maida-debug-gate` traces a failed report back to the behavioral change before
  deciding whether to fix the code or deliberately accept new behavior.

Each workflow starts by reading the project's own instructions and structure,
then leaves a reviewable local diff. It does not push commits or upload traces.
The pack does not claim to inject Maida automatically into arbitrary repositories.

Use the [coding-agent refactor demo](demos/coding_agent_refactor/) to see the
complete offline story: a plausible refactor still reports passing tests, but
Maida blocks it because the agent silently repeats the test command. OpenCode
users can pair the skills with the [Maida OpenCode plugin](https://github.com/maida-ai/opencode-plugin)
and its deterministic event-replay demo.

## Version policy

These tutorials intentionally track the latest Maida behavior. Install the current `maida-ai` package and `maida` CLI when running them; older Maida releases and older trace formats are not a compatibility target for this repo.

## Notebooks

### 1. Stop a Runaway Agent (`Guardrails/`)

**File:** `Guardrails/Stop a Runaway Agent.ipynb`
**Install:** `uv pip install maida-ai`

A minimal introduction using only the core Maida SDK with no framework dependencies. Builds a tiny local agent that loops on the same tool call and model call, then shows how to:

- Observe a `LOOP_WARNING` in the timeline without stopping the run
- Enable `stop_on_loop` to abort execution as soon as the pattern repeats
- Compare the two runs side by side in `maida view`

Good starting point if you want to understand guardrails before looking at framework integrations.

---

### 2. Debug a LangGraph Agent (`LangChain/`)

**File:** `LangChain/Mock LangGraph Agent.ipynb`
**Install:** `uv pip install "maida-ai[langchain]"`

Builds a multi-node LangGraph graph (search → calculate → save) using `FakeListLLM` and deterministic `@tool` functions. Covers:

- Adding `LangChainCallbackHandler` to a LangGraph run
- Verifying the exact happy-path signature: four LLM calls, three tool calls, and `search → calculator → save_result`
- A looping agent that triggers `LOOP_WARNING`
- Using `stop_on_loop` to abort the graph with `LOOP_WARNING → ERROR → RUN_END(status=error)`
- Missing dependencies, inactive-run behavior, normalized events, and Maida's storage redaction/truncation

---

### 3. Debug an OpenAI Agents Workflow (`OpenAI/`)

**File:** `OpenAI/Mock OpenAI Agent.ipynb`
**Install:** `uv pip install "maida-ai[openai]" openai-agents`

Uses the OpenAI Agents SDK tracing API (`generation_span`, `function_span`) with deterministic inputs to drive the same quarterly-sales workflow without hitting any real model endpoint. Covers:

- Registering the Maida OpenAI Agents tracing processor via `set_trace_processors`
- Verifying the exact happy-path signature: four LLM calls, three tool calls, and `search → calculator → save_result`
- A looping workflow that triggers `LOOP_WARNING`
- Using `stop_on_loop` to finish with `LOOP_WARNING → ERROR → RUN_END(status=error)`
- Missing dependencies, inactive-run behavior, normalized events, and Maida's storage redaction/truncation
- Using `PROCESSOR.abort_exception` polling as a compatibility fallback for the SDK version locked by the tutorial

---

### 4. Debug a CrewAI Workflow (`CrewAI/`)

**File:** `CrewAI/Mock CrewAI Agent.ipynb`
**Install:** `uv pip install "maida-ai[crewai]"`

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
uv pip install maida-ai jupyter

# For LangChain notebook
uv pip install "maida-ai[langchain]"

# For OpenAI Agents notebook
uv pip install "maida-ai[openai]" openai-agents

# For CrewAI notebook
uv pip install "maida-ai[crewai]"

# Start Jupyter
jupyter notebook
```

Open the notebook of your choice and run all cells in order. After each run, start the viewer in a terminal:

```bash
maida view
```
