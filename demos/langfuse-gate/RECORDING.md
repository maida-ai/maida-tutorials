# Record the Langfuse gate demo

The recording is designed to land in **30–60 seconds**. It is deterministic,
offline after installation, and pauses before each act so you control the
pacing without typing commands on camera.

## Prepare once

From `maida-tutorials/demos/langfuse-gate`:

```bash
uv sync --locked
uv run --frozen python demo.py
```

The automatic rehearsal should finish with `PR BLOCKED` and still exit `0`.
For the recording, use a terminal wide enough to keep the behavior-change table
on one line (roughly 110 columns), increase the font size, and clear the screen.

Keep the opening line visible. It labels the traces as synthetic while making
clear that the importer and gate are real.

## Record

Start the paced version:

```bash
uv run --frozen python demo.py --recording
```

Use this three-shot sequence:

1. **ACT 1 — Capture known-good behavior** (10–15 seconds). Press Enter and
   let the real `maida import langfuse` and `maida baseline` commands establish
   the one-tool `lookup_account` path.
2. **ACT 2 — Verify unchanged behavior** (8–12 seconds). Press Enter and hold
   briefly on `Maida verdict: pass`. This establishes that importing a later
   trace does not create a false regression.
3. **ACT 3 — Catch the regression** (15–25 seconds). Press Enter, then hold on
   the behavior table: one lookup became three `escalate_case` calls, a loop,
   twice the latency, and more than six times the tokens. End on `PR BLOCKED`.

The final spoken beat can stay literal: “Langfuse recorded what happened.
Maida caught what changed before merge.”

## Recording safeguards

- Do not replace the fixture credentials with real credentials; none are
  needed for this recording.
- Do not crop out the synthetic-data label.
- The server listens only on loopback and shuts down when the command exits.
- Runs and the baseline use a temporary directory that is deleted
  automatically.
- If a take is interrupted, rerun the same command; there is no cleanup step
  and no repository state to reset.
