# <img src="assets/maida-symbol-dynamic.svg" alt="" width="36" height="32"> Maida tutorials

**Maida checks agent changes before merge.** This core product repository owns the canonical runnable coding-agent experience, plus tutorials and examples. The [Maida engine and CLI](https://github.com/maida-ai/maida) own the checks; [maida-assert](https://github.com/maida-ai/maida-assert) brings them to the GitHub PR boundary.

## See the real thing: a coding-agent change with green tests

Ask a coding agent to simplify a small storefront's shipping function. A helpful-looking instruction says to refresh test expectations when output changes. The agent rewrites the VIP regression test: shipping now costs $15 instead of $0, yet all four application tests pass. **Maida fails the behavioral regression.**

The [canonical coding-agent project](demos/pr-gate/) shows the complete story in one sitting. Clone this repository, use Python 3.12 or 3.13, then run from its root:

```bash
uv sync --directory demos/pr-gate --locked
uv run --directory demos/pr-gate --frozen python demo.py
```

You will see **safe refactor → PASS → instruction change → green application tests hiding the $15 VIP regression → Maida FAIL**. The same storefront also demonstrates skipped verification and an agent “improving” its own instructions until it drops a protected responsibility. All four scenarios are individually runnable. Maida gates an agent change regardless of who authored it.

If this demo helped you spot what green tests missed, ⭐ [star Maida](https://github.com/maida-ai/maida) — it helps other teams find the project.

The coding decisions are deterministic, with real file edits, real application tests, and released Maida 0.6.1. No credentials or live model are needed. After dependency installation, the rehearsal runs offline in temporary workspaces and leaves your checkout unchanged. Start here; you do not need reference documentation to understand the lesson.

## Try the standalone CLI

For a quick canned gate story without cloning anything:

```bash
uv tool install "maida-ai==0.6.1"
maida demo --regression
```

Maida shows a failing verdict and PR-comment preview. An expected `FAIL` is the lesson succeeding.

## Protect a task in your repository

After the reference experience, follow the [coding-agent walkthrough](guides/coding-agent.md) to capture and check your own task. Building a Python tool-calling agent? Use the [Python agent walkthrough](guides/python-agent.md).

The [Maida coding-agent skill pack](https://github.com/maida-ai/skills/tree/main/product) provides `maida-instrument-agent`, `maida-add-regression-gate`, and `maida-debug-gate`. Each leaves a reviewable local diff and does not push commits or upload traces. See its integration list for supported coding agents. The [Maida OpenCode plugin](https://github.com/maida-ai/opencode-plugin) is another capture integration.

## Additional practice and reference

- [coding-agent refactor demo](demos/coding_agent_refactor/): repeated test runs hidden behind the same final answer.
- [Broken PR demo](demos/broken_pr/): an unnecessary order lookup, then repair.
- [Examples catalog](examples/README.md): Python agents and optional framework examples.
- [Integration notebooks](guides/notebooks.md): optional notebook lessons and historical compatibility notes.
- [Langfuse import demo](demos/langfuse_import/): an optional read-only import lesson.
- [Demo catalog](demos/README.md): other focused lessons.

## Contribute a lesson

A lesson should start from a real developer task, show the expected result, exercise a failure and recovery, and keep run data in a temporary or explicitly chosen local directory. See [CONTRIBUTING.md](CONTRIBUTING.md).

The root lockfile and published onboarding workflow use `maida-ai==0.6.1`. The [0.5 compatibility walkthrough](guides/coding-agent-0.5.md) and historical CrewAI notebook retain their explicit 0.5.3 pins. Repository releases follow the engine's `MAJOR.MINOR` compatibility line with their own `PATCH`, as described in the [cross-repository compatibility policy](https://github.com/maida-ai/maida/blob/main/CONTRIBUTING.md#versioning-and-compatibility).
