# Protect one coding task

Start with the [quickstart](https://maida.ai/docs/getting-started/) and its offline `maida demo --regression`. Then use a task in your own repository. Automatic local capture setup and `maida check` require Maida 0.6.1 or newer. You can stop after the first report and return to baseline review later.

## Checkpoint 1: check your normal work

Choose a short, read-only task: **“Find the command this repository uses to run its tests. Cite the configuration file that defines it. Do not edit files or install dependencies.”** Check the answer against that file. Use a repository you already understand so the task itself is small.

The supported hook integration records tool activity and lifecycle events. It does not provide complete model usage, token, or topology coverage. Maida stores this evidence locally; your coding agent still uses its usual model provider. An isolated CLI install is enough; the project can use any language. Use Python 3.12 or newer.

### Integration: Claude Code command hooks

Install the standalone CLI, then run setup inside your Git repository:

```bash
uv tool install "maida-ai==0.6.1"
cd /path/to/your/repo
maida init
```

Maida detects the agent environment, previews passive capture hooks and local setup files, and asks for approval before writing. For Claude Code, it uses `.claude/settings.local.json` and `.maida/local.json`, preserves shared settings and other hooks, and excludes local setup files from Git. It creates no policy or baseline. If detection is ambiguous, use `maida init --agent claude-code`. Noninteractive first-run setup previews changes and exits `2`; approve it from an interactive terminal.

If upgrading an older standalone CLI, use `uv tool install --force "maida-ai==0.6.1"`. Existing hooks may also need upgrading: follow init's recovery guidance, approve the preview, and restart the coding-agent session. Shared legacy hooks require `maida detach --agent claude-code` before init; user-wide hooks require removing the old Maida entries in the agent's `/hooks` menu. See the [init reference](https://maida.ai/docs/cli/init/) for inherited-hook handling.

Already installed Maida into the project's environment? Use `uv run maida init` and `uv run maida check`. Init binds hooks to that environment, so plain `claude` works afterward without Maida on the global PATH. Review the actual local files against the preview; Git diff omits ignored or untracked settings. Start a **new** session here, complete the short task, then exit normally:

```bash
claude
```

The session-end hook imports the completed run automatically. Check it immediately:

```bash
maida check
```

Expect your task's trace ID, a report checking successful completion, recorded loop warnings and recorded guardrail events, and the exact viewer command. No baseline or policy is needed; existing policy files do not affect `check`. These checks do not test answer correctness, forbid edits, or establish anything about unrecorded behavior. A recovered child failure remains visible in the error count without making a normally completed task fail the completion check.

Missing or unfinished newest capture exits `2` with recovery guidance instead of selecting an older task or an SDK run. If a check fails, follow the printed `maida view TRACE_ID` command to inspect that same task, fix the cause, and retry. When launched through uv, the printed command includes `uv run`. The [capture guide](https://maida.ai/docs/claude-code/) covers abrupt-exit recovery and richer exporter capture.

**This is the first useful checkpoint.** You have checked your own task and have local evidence to inspect. Capture defaults to `~/.maida/projects/<project-id>/`, outside Git; each initialized checkout has its own identity. A configured Maida storage override changes the parent while retaining project isolation. No storage environment variable is needed for this flow. To stop capture, run `maida detach --agent claude-code`, approve its preview, and restart the agent session. Saved evidence and other hooks are preserved; reconnect with `maida init --agent claude-code`.

## Checkpoint 2: review a small contract

Keep the task text, starting commit, agent/model versions, and configuration with your review. Check the installed command contract:

```bash
maida init --help
```

The explicit `--from-run` and `--reviewed --reason` workflow remains available. If you are using Maida 0.5.x, continue with the [0.5 compatibility walkthrough](coding-agent-0.5.md#checkpoint-2-review-a-small-contract); it accounts for that release's different comparison interface.

Draft from the known-good task using the trace ID printed by `maida check`. Replace `KNOWN_GOOD_TRACE_ID` below with that ID:

```bash
maida init --from-run KNOWN_GOOD_TRACE_ID
```

Check the printed workflow and trace ID. `--from-run latest` retains SDK/Python selection and could select a demo run instead of your captured task. Open `.maida/starter/policy.yaml`. It proposes at most three observed invariants: successful completion, no recorded loops, and no recorded guardrail events. Delete anything your task does not require; keep at least one meaningful requirement. The draft is inactive. One observed run is not a guarantee, and absent capture is not proof that an action never occurred.

Only after reviewing the candidates, accept them with your reason:

```bash
maida init --reviewed --reason "This test-command lookup must complete without recorded loops or guardrail stops"
```

Expect `.maida/policy.yaml`, `.maida/baselines/agent.json`, and a review record with the accepted hashes. No hand-written policy template or run-ID extraction is needed. Preserve those files for the next check.

## Checkpoint 3: check the next change

Repeat the same task from the same starting repository state in a fresh session, changing only the agent configuration or implementation you intend to compare:

```bash
claude
```

After normal session completion, run `check` and use its printed trace ID as `CANDIDATE_TRACE_ID` in the baseline comparison:

```bash
maida check
maida assert CANDIDATE_TRACE_ID --baseline .maida/baselines/agent.json --policy .maida/policy.yaml
```

Confirm that the new observation belongs to the same task before comparing. Baseline gates and bare `list` or `view` retain their SDK/Python storage defaults; the explicit captured trace ID selects your task. Read the verdict and individual checks. PASS applies to the selected evidence and policy; FAIL identifies a violation; INCONCLUSIVE requires more suitable evidence or an explicitly reviewed requirement. Exit zero alone is not approval.

Before relying on a requirement, reproduce a safe, relevant violation and repair it without changing the baseline. Do not induce dangerous actions in your repository. The offline [shipping refactor lab](../demos/pr-gate/) rehearses PASS → FAIL → repair when you do not have a safe real regression to repeat. Its stronger policy detects test rewriting; the small starter above does not claim that coverage. Follow the viewer command from `check` to investigate a failed observation.

## Checkpoint 4: add CI when the local check is useful

Use the [gate skill](https://github.com/maida-ai/skills/tree/main/product/maida-add-regression-gate) to make the same task repeatable with pinned versions and explicit budgets. Coding-agent CI needs a repeatable scenario, not a saved session. The [init reference](https://maida.ai/docs/cli/init/) also shows generating a workflow for an existing traced Python entrypoint.

Before treating the GitHub check as a merge gate, test it on an actual PR, including a fresh result on the new head after intentional acceptance. Configure required checks and workflow-file review protection. Acceptance must preserve the reviewed reason and evidence; do not replace a baseline just to get green.
