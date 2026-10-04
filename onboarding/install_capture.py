"""Historical 0.5 capture setup; use maida init with Maida 0.6.1 or newer."""

from __future__ import annotations

import argparse
import copy
import json
import os
import tempfile
from pathlib import Path

EVENTS = (
    "SessionStart",
    "PreToolUse",
    "PostToolUse",
    "PostToolUseFailure",
    "PermissionDenied",
    "SessionEnd",
)
COMMAND = "maida capture claude-hook"


def merged_settings(settings: dict) -> tuple[dict, list[str]]:
    """Preserve existing settings; add one observer per missing lifecycle event."""
    result = copy.deepcopy(settings)
    hooks = result.setdefault("hooks", {})
    if not isinstance(hooks, dict):
        raise ValueError("settings.hooks must be an object")
    added = []
    for event in EVENTS:
        groups = hooks.setdefault(event, [])
        if not isinstance(groups, list):
            raise ValueError(f"hooks.{event} must be a list")
        for group in groups:
            if not isinstance(group, dict) or not isinstance(group.get("hooks"), list):
                raise ValueError(f"hooks.{event} contains an invalid hook group")
            if any(not isinstance(hook, dict) for hook in group["hooks"]):
                raise ValueError(f"hooks.{event} contains an invalid hook")
        # A hook restricted to a matcher does not cover this lifecycle event.
        if any(
            group.get("matcher", "") in ("", "*")
            and any(
                hook.get("type") == "command" and hook.get("command") == COMMAND
                for hook in group["hooks"]
            )
            for group in groups
        ):
            continue
        groups.append({"hooks": [{"type": "command", "command": COMMAND}]})
        added.append(event)
    return result, added


def install(project: Path, *, apply: bool) -> list[str]:
    project = project.resolve(strict=True)
    directory = project / ".claude"
    path = directory / "settings.json"
    if directory.is_symlink() or path.is_symlink():
        raise ValueError(
            "Refusing symlinked .claude/settings.json or .claude directory"
        )
    settings = json.loads(path.read_text()) if path.exists() else {}
    if not isinstance(settings, dict):
        raise ValueError("settings.json must contain an object")
    merged, added = merged_settings(settings)
    if not apply or not added:
        return added
    directory.mkdir(exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=".maida-settings-", dir=directory)
    try:
        with os.fdopen(descriptor, "w") as stream:
            json.dump(merged, stream, indent=2)
            stream.write("\n")
        if path.exists():
            os.chmod(temporary, path.stat().st_mode & 0o777)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)
    return added


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path.cwd())
    parser.add_argument(
        "--apply", action="store_true", help="Write the previewed additions"
    )
    arguments = parser.parse_args()
    try:
        added = install(arguments.project, apply=arguments.apply)
    except (OSError, ValueError) as error:
        parser.exit(
            2, f"Cannot configure capture: {error}. Fix the settings and retry.\n"
        )
    if not added:
        print("Maida capture hooks are already configured; no changes.")
    else:
        verb = "Added" if arguments.apply else "Would add"
        print(f"{verb} observer command: {COMMAND}")
        print("Events: " + ", ".join(added))
        print(
            "Open .claude/settings.json and review it against the preview before starting a new session. Git diff omits ignored or untracked files."
            if arguments.apply
            else "Rerun with --apply to write these additions."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
