# One home for learning Maida

`maida-tutorials` owns tutorials, runnable examples, and demos. The old Demos repository becomes a redirect; the engine keeps production code, integration implementation, contracts, and their tests.

The [machine-readable inventory](migration-inventory.json) records every migrated tracked file, its source repository and commit, original SHA-256, and destination. Files were copied and byte-verified before path adjustments. Subsequent changes adapt workflow paths and learning material; the recorded digest describes the source artifact, not an immutable destination.

- `maida-ai/Demos/pr-gate` moved to `demos/pr-gate`.
- `maida-ai/Demos/langfuse-gate` moved to `demos/langfuse-gate`.
- `maida-ai/Demos/agent-behavior-gates` moved to `demos/agent-behavior-gates`.
- `maida-ai/Demos/injection-arena` moved to `demos/injection-arena` as an archived experiment.
- Demos workflows moved to this repository's `.github/workflows` with their path filters and commands updated.
- `maida-ai/maida/examples` moved to `examples`, preserving its subdirectories.

Only tracked source assets were migrated. Environment files, virtual environments, local runs, repositories, and untracked user files were excluded. Licenses and third-party notices remain beside the examples they describe.

Repository archive settings and remote redirects require a later publication step; these local commits do not change GitHub's repository settings.
