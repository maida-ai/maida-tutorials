# Catch a coding-agent regression before merge

This offline demo simulates a coding agent making a plausible refactor. Both
versions inspect the repository, edit one module, report 12 passing tests, and
return the same final answer. The broken version silently runs the identical
test command three times. Maida catches the extra tool work and loop before the
change merges.

Nothing in the demo modifies your source tree. It uses fixed local data, makes
no network calls, and requires no API key, hosted model, or coding-agent
account.

## Run the known-good refactor

From the repository root, install the locked environment and record the
efficient execution path:

```bash
UV_CACHE_DIR=/tmp/uv-cache uv sync --locked
MAIDA_DATA_DIR=.maida/coding-agent-runs uv run python \
  demos/coding_agent_refactor/refactoring_agent.py --mode good
MAIDA_DATA_DIR=.maida/coding-agent-runs uv run maida assert \
  --baseline .maida/baselines/coding-agent-refactor.json \
  --policy .maida/policy.yaml \
  --format markdown
```

The simulated agent prints `Refactor complete; 12 tests passed.` The gate exits
with exit code `0` because the run matches the committed baseline: one
`inspect_repository`, one `edit_module`, and one `run_tests` tool call.

## Reproduce the regression

Now run the refactored agent with its repeated-test bug:

```bash
MAIDA_DATA_DIR=.maida/coding-agent-runs uv run python \
  demos/coding_agent_refactor/refactoring_agent.py --mode regression
MAIDA_DATA_DIR=.maida/coding-agent-runs uv run maida assert \
  --baseline .maida/baselines/coding-agent-refactor.json \
  --policy .maida/policy.yaml \
  --format markdown
```

The final answer is unchanged, but the gate exits with exit code `1`. Maida
reports five tool calls instead of three and identifies the three identical
`run_tests` calls as a loop. This is the pre-merge distinction: answer-quality
checks can miss a process regression that a behavioral regression gate sees.

Maida commands default to the latest run, so the workflow does not need run-ID
extraction. Fix the repeated work and rerun the gate. If the behavior was
intentional, inspect the structural diff and policy impact before accepting a
new baseline; never update a baseline merely to make the check green.

## Use this workflow with a coding agent

The canonical [Maida coding-agent skills](https://github.com/maida-ai/skills/tree/main/product)
walk an agent through instrumentation, adding the baseline and CI gate, and
debugging a failed report while keeping every change reviewable and local.
Maida does not inject itself into arbitrary repositories: you explicitly
install a skill, review its proposed edits, and run the local checks.

For OpenCode, see the [Maida OpenCode plugin](https://github.com/maida-ai/opencode-plugin)
and its deterministic event-replay variant of this scenario.
