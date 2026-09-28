"""Active-arena context, isolated to avoid import cycles.

The mock tools run inside the OpenAI Agents runtime and need the current
``Arena`` without it appearing in any tool schema. Keeping the ContextVar in a
dependency-free module lets both ``arena`` and ``mock_tools`` import it.
"""

from __future__ import annotations

import contextvars
from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from .arena import Arena

_current: contextvars.ContextVar["Arena | None"] = contextvars.ContextVar(
    "current_arena", default=None
)


def set_arena(arena: "Arena") -> None:
    _current.set(arena)


def current_arena() -> "Arena":
    arena = _current.get()
    if arena is None:  # pragma: no cover - tools always run inside a round
        raise RuntimeError("No active arena in this context")
    return arena
