# Contributing a tutorial

Start with a developer task and one observable checkpoint. Explain the next safe action for a failed step. A good lesson contains a passing run, one realistic change that fails, the reason it failed, and a repair. Mark simulated decisions, live services, historical compatibility, and development-only commands at the point of use.

Use the [released coding-agent route](https://maida.ai/docs/getting-started/) as the default entry and the Python route as a secondary link. New examples belong here, not in the engine or the former Demos repository. Keep notebooks optional. Install only what the selected lesson needs.

Run the core tutorial suite and released user workflow separately:

```bash
uv sync --locked
uv run --frozen python -m unittest discover -s tests
uv run --no-project --with "maida-ai==0.6.0" python -m unittest discover -s onboarding/tests
```

The released workflow test uses temporary project directories and replays capture protocol events; it never invokes a model. It proves the documented CLI contract, not a live coding agent or GitHub branch protection. Run each changed independent demo's own suite from its directory as well.

Use the existing lockfiles and keep imported licenses. Do not silently lower a reviewed policy to make a lesson pass. When moving a file, keep the migration inventory and inbound documentation links accurate.
