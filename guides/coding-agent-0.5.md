# Coding-agent compatibility: Maida 0.5.x

Use this compatibility guide only with Maida 0.5.x. For the shorter reviewed setup in Maida 0.6 and newer, use [Protect one coding task](coding-agent.md). This walkthrough uses `maida-ai==0.5.3` and an actual task in your repository. Your normal coding agent may call its model provider; Maida keeps captured evidence locally. Pick one small, repeatable task, such as changing a validation message while preserving the tests. Keep its task text, starting commit, agent version, model, and configuration together so later runs are comparable.

## Checkpoint 1: capture your normal work

The supported hook integration below records tool activity and lifecycle events. It does not provide complete model usage, token, or topology coverage. An isolated Maida tool install is enough for this capture path; the project can use any language.

### Integration: Claude Code command hooks

Install the released CLI and get the tutorial helper once:

```bash
uv tool install "maida-ai==0.5.3"
git clone https://github.com/maida-ai/maida-tutorials.git
export MAIDA_TUTORIALS="$PWD/maida-tutorials"
```

Run the helper with the path to your project. Preview is read-only; `--apply` adds passive observers while preserving existing settings and hooks. These hooks never approve or deny an agent action.

```bash
uv run --no-project python "$MAIDA_TUTORIALS/onboarding/install_capture.py" --project /path/to/your/repo
uv run --no-project python "$MAIDA_TUTORIALS/onboarding/install_capture.py" --project /path/to/your/repo --apply
```

In your project, open `.claude/settings.json` and compare it with the helper preview. `git diff -- .claude/settings.json` shows changes only when that file is already tracked; an empty diff is not evidence that nothing changed. Keep ignored or untracked settings local unless you deliberately choose to version them. Ensure `maida --version` works in the terminal that launches the agent. Set one local evidence directory before starting a **new** session, complete the selected task, and exit normally:

```bash
cd /path/to/your/repo
export MAIDA_DATA_DIR="$PWD/.maida/known-good"
claude
```

The session-end hook imports the completed run automatically. The checkpoint is `maida list` showing a completed run. Add `.maida/known-good/` and `.maida/candidate/` to your project's `.gitignore`; these contain local evidence, not source configuration. If no run appears, verify the hook command is on PATH and the session ended. The [capture guide](https://maida.ai/docs/claude-code/) covers exporter capture and abrupt-exit recovery.

## Checkpoint 2: review a small contract

Generate a draft from that observed task:

```bash
maida extract --window .maida/known-good/runs --out .maida/draft
```

The command prints the workflow directory containing `baseline.json` and `policy.yaml`. Open that directory and review the evidence. The draft is inactive, may contain tight numerical bounds from one observation, and must not be treated as an accepted specification. For a first gate, keep only a few checks you understand: a tool required by this particular task, successful completion, and no observed guardrail events are candidates only when the capture actually records them. A hook capture's lack of model usage is no evidence that a model made zero calls.

For this small tutorial contract, capture the known-good run as the baseline:

```bash
maida baseline --out .maida/baselines/coding-task.json
```

After reviewing the observations, create `.maida/policy.yaml` with the candidates you explicitly accept. This example is appropriate only if the task actually used `Read`, reviewing that content is required, and all three observations and their coverage fit your task. Replace `Read` with the observed required tool or omit that candidate; never invent a requirement to fill the template:

```yaml
# Reviewed for the selected coding task; observed runs are not a guarantee.
version: 2
metrics:
  required_tools: {kind: invariant, all_of: [Read]}
  no_guardrails: {kind: invariant, require: true}
  stop_condition_reached: {kind: invariant, require: true}
```

Record your reason, the task and starting commit, agent/model/configuration versions, and the observation limits alongside the baseline. Keep the invariant policy small; do not add a list of forbidden tools your repository does not use. The checkpoint is a reviewed baseline and policy in your local diff, with no trace payload committed.

## Checkpoint 3: check the next change

Use the same task from a fresh copy of the same starting state, changing only the configuration or implementation under test. Keep the baseline evidence separate. In the terminal for that new session:

```bash
export MAIDA_DATA_DIR="$PWD/.maida/candidate"
claude
```

After the session ends, explicitly confirm it performed the same task from the same starting state, then evaluate the new evidence:

```bash
uv run --no-project --with "maida-ai==0.5.3" python "$MAIDA_TUTORIALS/onboarding/gate_capture.py" --window .maida/candidate/runs --baseline .maida/baselines/coding-task.json --policy .maida/policy.yaml --same-task
```

The release names each capture by session, so this helper explicitly maps one reviewed task across those identities. It delegates to the released three-verdict evaluator, preserves the original files, and reports the source identities and baseline hash. It refuses mixed-session windows; use a fresh evidence directory for each comparison. Do not substitute the release's legacy `maida assert`: it omits v2 invariant metrics.

Read the verdict itself: `PASS` means the configured checks passed on the observed candidate window; `FAIL` names a broken contract; `INCONCLUSIVE` means evidence was insufficient. Exit zero alone does not mean approval. The checkpoint is a readable report with the next action you can take.

Practice failure and repair in the [shipping refactor lab](../demos/pr-gate/) if you do not yet have a safe real regression to reproduce. Its stronger reviewed policy catches test rewriting; the three-check starter above does not claim to detect that behavior. Fix the cause and recapture a fresh candidate. For an intentional change, review the evidence and use the [acceptance workflow](https://maida.ai/docs/regression-testing/); do not replace the baseline just to get a green check.

## Checkpoint 4: add CI after local evidence works

Use the [gate skill](https://github.com/maida-ai/skills/tree/main/product/maida-add-regression-gate) to make the same task repeatable in CI with pinned versions and explicit budgets. The released `maida init --github` emits a scaffold that still needs a real capture/agent command and reviewed baseline. Observed-run `init` options require Maida 0.6 or newer.

Before treating a GitHub check as a merge gate, test it on an actual PR in your repository, including a changed PR head after deliberate acceptance. Configure required checks and workflow-file review protection. A local report or the tutorials' CI cannot establish your repository's merge boundary.

To investigate a failed check, run `maida view` against the candidate evidence, compare the changed behavior, and rerun after the fix. You can stop at any checkpoint and continue from the files you already reviewed.
