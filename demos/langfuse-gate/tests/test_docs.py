from pathlib import Path


DEMO_DIR = Path(__file__).resolve().parents[1]
REPO_ROOT = DEMO_DIR.parents[1]


def test_readme_covers_offline_recording_and_real_langfuse_usage():
    readme = (DEMO_DIR / "README.md").read_text(encoding="utf-8")
    for expected in (
        "uv run --frozen python demo.py",
        "uv run --frozen python demo.py --recording",
        "synthetic",
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "maida import langfuse --trace-id",
        "No Langfuse account",
        "read-only",
        "PR BLOCKED",
    ):
        assert expected in readme


def test_recording_guide_has_a_short_rehearsable_shot_list():
    guide = (DEMO_DIR / "RECORDING.md").read_text(encoding="utf-8")
    for expected in (
        "30–60 seconds",
        "--recording",
        "ACT 1",
        "ACT 2",
        "ACT 3",
        "PR BLOCKED",
        "synthetic",
    ):
        assert expected in guide


def test_github_actions_example_uses_one_trusted_imported_trace():
    workflow = (DEMO_DIR / "examples" / "github-actions.yml").read_text(
        encoding="utf-8"
    )
    for expected in (
        "LANGFUSE_PUBLIC_KEY",
        "LANGFUSE_SECRET_KEY",
        "LANGFUSE_TRACE_ID",
        "trace-command:",
        'maida import langfuse --trace-id "$LANGFUSE_TRACE_ID"',
        "baseline:",
        "policy:",
    ):
        assert expected in workflow
    assert "--from" not in workflow


def test_active_ci_is_path_filtered_to_the_langfuse_demo():
    workflow = (REPO_ROOT / ".github" / "workflows" / "langfuse-gate.yml").read_text(
        encoding="utf-8"
    )
    assert '"demos/langfuse-gate/**"' in workflow
    assert "uv sync --directory demos/langfuse-gate --locked" in workflow
    assert "uv run --directory demos/langfuse-gate --frozen pytest -q" in workflow
    assert "uv run --directory demos/langfuse-gate --frozen python demo.py" in workflow
