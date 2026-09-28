"""Deterministic offline path.

Used when running without an OpenAI key (or with ``ARENA_FORCE_CANNED=1``). The
warmup replays the active scenario's known-good tool calls through the real tool
path so the baseline behavior - and everything downstream - is identical to a
live run. Attack injections and fallbacks live on the scenario's rounds.
"""

from __future__ import annotations

from . import mock_tools


async def warmup(arena) -> None:
    """Replay the scenario's known-good, on-task behavior."""
    scenario = arena.scenario
    await arena.emit("worker_msg", text=scenario.warmup_intro)
    for tool_name, kwargs in scenario.warmup_calls:
        await mock_tools.IMPL_BY_NAME[tool_name](**kwargs)
    await arena.emit("worker_msg", text=scenario.warmup_outro)
