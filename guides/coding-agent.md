# Protect one coding task

Start with the [quickstart](https://maida.ai/docs/getting-started/) and its offline `maida demo --regression`. Then use a task in your own repository. Allow 10–15 minutes for capture setup and the first useful report below; this is a setup target, not a measured completion time. You can stop after that report and return to baseline review later.

## Checkpoint 1: check your normal work

Choose a short, read-only task: **“Find the command this repository uses to run its tests. Cite the configuration file that defines it. Do not edit files or install dependencies.”** Check the answer against that file. Use a repository you already understand so the task itself is small.

The supported hook integration records tool activity and lifecycle events. It does not provide complete model usage, token, or topology coverage. Maida stores this evidence locally; your coding agent still uses its usual model provider. An isolated CLI install is enough; the project can use any language. Use Python 3.12 or newer.

### Integration: Claude Code command hooks

Install the CLI and get the capture helper once:

```bash
uv tool install "maida-ai==0.5.3"
git clone https://github.com/maida-ai/maida-tutorials.git
export MAIDA_TUTORIALS="$PWD/maida-tutorials"
```

Preview the capture setup for your repository, then apply the reviewed change. The helper preserves existing settings and hooks and adds passive observers; these hooks never approve or deny an agent action.

```bash
uv run --no-project python "$MAIDA_TUTORIALS/onboarding/install_capture.py" --project /path/to/your/repo
uv run --no-project python "$MAIDA_TUTORIALS/onboarding/install_capture.py" --project /path/to/your/repo --apply
```

In your repository, open `.claude/settings.json` and compare it with the helper preview. `git diff -- .claude/settings.json` shows changes only when that file is already tracked; an empty diff is not evidence that nothing changed. Keep ignored or untracked settings local unless you deliberately choose to version them. Ensure `maida --version` works in the terminal that launches the agent. Start a **new** session with isolated evidence, complete the short task, then exit normally:

```bash
cd /path/to/your/repo
export MAIDA_DATA_DIR="$PWD/.maida/known-good"
claude
```

The session-end hook imports the completed run automatically. Check it immediately:

```bash
maida list
maida assert --expect-status ok --no-loops --no-guardrails
```

Expect your completed task and a report checking completion, recorded loop warnings, and recorded guardrail events. No baseline or policy file is needed for this first report. These flags explicitly select those requirements; they do not test answer correctness, forbid edits, or establish anything about unrecorded behavior. If this repo already has a Maida policy, inspect it first: `assert` also loads `.maida/policy.yaml` when present.

If no completed run appears, confirm the hook command is on PATH and the session ended before adding anything else. If a check fails, use `maida view` to inspect the observation, fix the cause, and retry the short task. The [capture guide](https://maida.ai/docs/claude-code/) covers abrupt-exit recovery and richer exporter capture.

**This is the first useful checkpoint.** You have checked your own task, have a local report, and know where its evidence lives. Add `.maida/known-good/` and `.maida/candidate/` to `.gitignore`; they contain local evidence. Continue when you want a contract for the next agent change.

## Checkpoint 2: review a small contract

Keep the task text, starting commit, agent/model versions, and configuration with your review. Check the installed command contract:

```bash
maida init --help
```

If help includes `--from-run`, use the reviewed workflow below (Maida 0.6 and newer). If you are using Maida 0.5.x, continue with the [0.5 compatibility walkthrough](coding-agent-0.5.md#checkpoint-2-review-a-small-contract); it accounts for that release's different comparison interface.

Draft from the known-good task, with `MAIDA_DATA_DIR` still selecting its evidence:

```bash
maida init --from-run latest
```

Check the printed workflow and trace ID. Open `.maida/starter/policy.yaml`. It proposes at most three observed invariants: successful completion, no recorded loops, and no recorded guardrail events. Delete anything your task does not require; keep at least one meaningful requirement. The draft is inactive. One observed run is not a guarantee, and absent capture is not proof that an action never occurred.

Only after reviewing the candidates, accept them with your reason:

```bash
maida init --reviewed --reason "This test-command lookup must complete without recorded loops or guardrail stops"
```

Expect `.maida/policy.yaml`, `.maida/baselines/agent.json`, and a review record with the accepted hashes. No hand-written policy template or run-ID extraction is needed. Preserve those files for the next check.

## Checkpoint 3: check the next change

Repeat the same task from the same starting repository state in a fresh session, changing only the agent configuration or implementation you intend to compare. Keep candidate evidence separate:

```bash
export MAIDA_DATA_DIR="$PWD/.maida/candidate"
claude
```

After normal session completion, inspect the selected run and evaluate it:

```bash
maida list
maida assert --baseline .maida/baselines/agent.json --policy .maida/policy.yaml
```

Confirm that the new observation belongs to the same task before comparing. Read the verdict and individual checks. PASS applies to the selected evidence and policy; FAIL identifies a violation; INCONCLUSIVE requires more suitable evidence or an explicitly reviewed requirement. Exit zero alone is not approval.

Before relying on a requirement, reproduce a safe, relevant violation and repair it without changing the baseline. Do not induce dangerous actions in your repository. The offline [shipping refactor lab](../demos/pr-gate/) rehearses PASS → FAIL → repair when you do not have a safe real regression to repeat. Its stronger policy detects test rewriting; the small starter above does not claim that coverage. Use `maida view` to investigate a failed observation.

## Checkpoint 4: add CI when the local check is useful

Use the [gate skill](https://github.com/maida-ai/skills/tree/main/product/maida-add-regression-gate) to make the same task repeatable with pinned versions and explicit budgets. Coding-agent CI needs a repeatable scenario, not a saved session. The [init reference](https://maida.ai/docs/cli/init/) also shows generating a workflow for an existing traced Python entrypoint.

Before treating the GitHub check as a merge gate, test it on an actual PR, including a fresh result on the new head after intentional acceptance. Configure required checks and workflow-file review protection. Acceptance must preserve the reviewed reason and evidence; do not replace a baseline just to get green.
