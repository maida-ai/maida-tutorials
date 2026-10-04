# Check your coding agent before merge

**A good-looking answer and green tests can hide an agent that worked worse.** Maida checks the agent's execution behavior alongside your tests of the result. Start with one normal task in your own repository, then protect the next change.

## Try Maida on your own task

Use Python 3.12–3.14 and an existing Git repository with Claude Code. Your project can use any language:

```bash
uv tool install "maida-ai==0.6.1"

cd my-repo
maida init

# Run one normal Claude Code task and exit the session.

maida check
# Follow the printed:
maida view <TRACE_ID>
```

Approve init's setup preview, then start a **new** session with `claude`. Complete a normal task and exit normally. For a short first task, ask: **“Find this repository's test command and cite the configuration file that defines it. Do not edit files or install dependencies.”** Check the answer yourself.

**Success looks like `3 active checks passed`**, your task's trace ID, and the exact viewer command. Replace `<TRACE_ID>` with that ID and inspect the same task's timeline. No tutorial clone, hook installer, or agent-code changes are needed.

**Runs on your machine or CI runner. No Maida cloud account required.** Task evidence is not uploaded to Maida; your agent's normal provider use, permissions, and costs are separate.

If Maida is installed in the project's uv environment, use `uv run maida init`, `uv run maida check`, and the printed `uv run maida view <TRACE_ID>`. Init connects that installation to the agent, so plain `claude` works afterward.

## Investigate a failed check

**Follow `maida view <TRACE_ID>` from the report**, inspect the failure and tool sequence, repair the cause, and repeat the task. Missing or unfinished newest capture gives recovery guidance instead of selecting an older task.

The first check requires successful completion, no recorded loops, and no recorded guardrail events. It does not compare a baseline or apply an existing policy. Capture observes tool activity and lifecycle, not answer correctness or complete model-call, token, or latency coverage. A recovered child failure remains visible without failing a normally completed task.

## Protect the next agent change

**Keep the behavior you reviewed, then compare the next change.** Instructions, skills, tools, model configuration, harness code, and application code can all change behavior. Maida gates the resulting change whether a human or the agent authored it.

Keep the task text, starting commit, agent/model versions, and configuration with your review. Choose a successful observation you understand. Use its trace ID from `maida check`:

```bash
maida init --from-run <TRACE_ID>
```

Review `.maida/starter/policy.yaml`. It proposes up to three requirements: successful completion, no recorded loops, and no recorded guardrail events. Delete anything your task does not require; keep at least one meaningful check. The draft is inactive, and the observed requirements are **candidates until you accept them**. One task is not a guarantee about future or unrecorded behavior.

After reviewing the requirements, accept them with a reason:

```bash
maida init --reviewed --reason "This test-command lookup must finish without recorded loops or guardrail stops"
```

Expect `.maida/policy.yaml`, `.maida/baselines/agent.json`, and a review record with accepted hashes. Keep those files for the next comparison.

### Check the next change

Repeat the same task from the same starting repository state in a fresh session, changing only the agent configuration or implementation you intend to compare. Exit normally, then:

```bash
maida check
# Use the new trace ID from this report:
maida assert <CANDIDATE_TRACE_ID> --baseline .maida/baselines/agent.json --policy .maida/policy.yaml
```

Read the verdict and individual checks: **PASS** applies to the selected evidence and requirements; **FAIL** identifies a violation; **INCONCLUSIVE** needs more suitable evidence or a reviewed requirement. Exit zero alone is not approval. Pass the captured task ID explicitly: bare assertions and `--from-run latest` retain SDK/Python selection and could choose an unrelated run.

Reproduce one safe, relevant failure and repair it without changing the baseline. Add reviewed requirements for any responsibility you need to protect; the small starter does not automatically protect test execution or detect test rewriting.

## See green tests approve a broken change

The [canonical storefront demo](../demos/pr-gate/) makes the difference visible: a coding agent rewrites the VIP regression test to approve **$15 shipping instead of $0**. All four application tests pass. **Maida fails the agent change** because its reviewed policy protects the regression test. The same project demonstrates skipped verification and an agent weakening its own instructions.

This deterministic rehearsal uses released Maida v0.6.1 and runs offline after installation. It is optional practice. For a smaller canned report without a clone, run `maida demo --regression`; expect FAIL and a PR-comment preview. The rehearsal exits `0` for that expected result.

## Add the PR gate when local protection works

Use the [gate skill](https://github.com/maida-ai/skills/tree/main/product/maida-add-regression-gate) to make the task repeatable with pinned versions and explicit budgets. CI needs a repeatable scenario, not a saved interactive session. Then follow the [Action setup and repository protection](https://github.com/maida-ai/maida-assert#add-the-merge-boundary).

Test the gate on an actual PR, including a fresh result on the new head after intentional acceptance. Configure required checks and workflow-file review protection. Keep the reviewed reason and evidence; do not replace a baseline just to get green.

## Setup help and reference

Init previews automatic local setup and preserves existing settings and other hooks. If detection is ambiguous, use `maida init --agent claude-code`. First-run setup needs an interactive terminal; noninteractive setup previews changes and exits `2`.

Upgrade an older standalone install with `uv tool install --force "maida-ai==0.6.1"`, rerun init, and follow its recovery guidance. Restart the agent session afterward. To stop capture, run `maida detach --agent claude-code`, approve the preview, and restart. Other hooks and saved evidence are preserved; reconnect with `maida init --agent claude-code`.

See the [getting started guide](https://maida.ai/docs/getting-started/), [init reference](https://maida.ai/docs/cli/init/) for inherited-hook recovery and review details, and [capture guide](https://maida.ai/docs/claude-code/) for coverage and abrupt exits. For another integration, use the [integration overview](https://maida.ai/docs/integrations/) or secondary [Python walkthrough](python-agent.md).
