# Protect one Python agent task

Begin with `uv tool install "maida-ai==0.5.3"` and `maida demo --regression` to see a failing gate and its report. Then add Maida to the interpreter that actually runs your project:

```bash
uv add "maida-ai==0.5.3"
```

A tool install does not make `import maida` available to your project's Python interpreter. Start with one task that uses a real tool you care about; wrap that entrypoint with `@trace` and record the tool call around its existing result. For a runnable starting point, use [examples/minimal/simple_agent.py](../examples/minimal/simple_agent.py). The [examples catalog](../examples/README.md) lists framework adapters when you need one.

## Capture and review the first run

Use the actual path to your entrypoint in the command below:

```bash
export MAIDA_DATA_DIR="$PWD/.maida/known-good"
uv run python your_agent.py
uv run maida extract --window .maida/known-good/runs --out .maida/draft
```

Review the generated baseline and candidate policy for the observed task. Follow [checkpoint 2 of the coding-agent walkthrough](coding-agent.md#checkpoint-2-review-a-small-contract) to keep the initial contract small and record explicit acceptance. Ignore evidence directories in Git; commit only the reviewed baseline, policy, and intended configuration.

## Reproduce a regression, then repair it

Run a changed version from the same starting state with `MAIDA_DATA_DIR="$PWD/.maida/candidate"`, then evaluate that candidate window with `uv run maida drift`. Use the exact baseline and policy paths you reviewed. Read the verdict and failing reason before deciding whether the code or intended contract should change.

The [order-status lesson](../demos/broken_pr/) walks through a concrete repeated-lookup failure and its repair with no model calls. It uses the repository's locked development environment for its strict policy; it is a practice lab, not a requirement for the released route.

Once pass, fail, and repair are repeatable locally, add CI using the [gate skill](https://github.com/maida-ai/skills/tree/main/product/maida-add-regression-gate). Keep the project environment, Maida version, task, and reviewed policy consistent between your terminal and CI.
