"""Run one recording take using the checkout's current AGENTS.md."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from coding_agent import REFRESH_EXPECTATIONS_RULE
from demo import (
    PROJECT_ROOT,
    Palette,
    _run_maida_gate,
    _show_agent_execution,
)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable ANSI colors",
    )
    parser.add_argument(
        "--agents-file",
        type=Path,
        default=PROJECT_ROOT / "AGENTS.md",
        help=argparse.SUPPRESS,
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    agents_source = args.agents_file.resolve()
    if not agents_source.is_file():
        print(f"recording demo error: missing {agents_source}", file=sys.stderr)
        return 2

    instructions = " ".join(agents_source.read_text(encoding="utf-8").split())
    candidate = REFRESH_EXPECTATIONS_RULE in instructions
    palette = Palette(enabled=not args.no_color and sys.stdout.isatty())

    state = "CHANGED instructions detected" if candidate else "original instructions"
    print(palette.title(f"CURRENT AGENTS.md — {state}"))
    try:
        _show_agent_execution(
            palette,
            candidate=candidate,
            agents_source=agents_source,
        )
        _run_maida_gate(
            palette,
            candidate=candidate,
            agents_source=agents_source,
        )
    except RuntimeError as error:
        print(f"recording demo error: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
