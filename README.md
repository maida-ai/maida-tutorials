# Maida tutorials

Don't let broken agent changes merge. Start with the [released coding-agent onboarding route](https://maida.ai/docs/getting-started/), then use one short lesson at a time here. This repository owns Maida's runnable examples, tutorials, and demos.

## See the gate once

Use Python 3.12 or 3.13 for the walkthroughs and maintained labs.

```bash
uv tool install "maida-ai==0.5.3"
maida demo --regression
```

No checkout or API key is needed. The simulated agent keeps a plausible final answer while repeating work; Maida shows a failing verdict and PR-comment preview. An expected `FAIL` is the lesson succeeding. This does not gate your project yet.

## Protect one real task

Follow the [coding-agent walkthrough](guides/coding-agent.md). It takes you through one normal task in your own repository, review of what was observed, a local gate, and one deliberately broken change. Stop after any checkpoint; you do not need to read the integration reference first.

Building a Python tool-calling agent? Use the [Python agent walkthrough](guides/python-agent.md) instead.

## Practice before changing your project

- [Shipping refactor lab](demos/pr-gate/): a realistic small project, real tests, and a deterministic coding harness. See why editing a test to hide a defect deserves a failed check.
- [coding-agent refactor demo](demos/coding_agent_refactor/): find repeated test runs hidden behind the same final answer.
- [Broken PR demo](demos/broken_pr/): reproduce an unnecessary order lookup, then repair it.

The practice labs explicitly simulate agent decisions and use pinned development snapshots where noted. They complement the released onboarding route; they do not establish that your live agent or GitHub branch protection works.

## Go deeper when you need it

- [Examples catalog](examples/README.md): minimal Python, framework adapters, and advanced examples migrated from the engine.
- [Integration notebooks](guides/notebooks.md): optional notebook lessons and historical compatibility notes.
- [Langfuse import demo](demos/langfuse_import/): read-only import using a local fake API.
- [Demo catalog](demos/README.md): trace imports, behavior contracts, and archived experiments.
- [Migration inventory](MIGRATION.md): where the former Demos repository and engine examples went.

The [Maida coding-agent skill pack](https://github.com/maida-ai/skills/tree/main/product) provides `maida-instrument-agent`, `maida-add-regression-gate`, and `maida-debug-gate`. Each leaves a reviewable local diff and does not push commits or upload traces. See its integration list for supported coding agents. The [Maida OpenCode plugin](https://github.com/maida-ai/opencode-plugin) is another capture integration.

## Contribute a lesson

A lesson should start from a real developer task, state its checkpoint, show the expected result, exercise one failure and recovery, and keep all run data in a temporary or explicitly chosen local directory. See [CONTRIBUTING.md](CONTRIBUTING.md).

The root lockfile pins an immutable development engine revision for the older reference labs, including restored `no_new_tools` behavior. The released route and its workflow test independently pin `maida-ai==0.5.3`. Do not present a development command as released onboarding. Repository releases follow the engine's `MAJOR.MINOR` compatibility line with their own `PATCH`, as described in the [cross-repository compatibility policy](https://github.com/maida-ai/maida/blob/main/CONTRIBUTING.md#versioning-and-compatibility).
