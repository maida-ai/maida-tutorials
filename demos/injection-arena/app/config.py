"""Runtime configuration and secret loading.

Local-first: we look for an OpenAI key in the environment first, then fall back
to the shared ``.env.secret`` two levels up (the Maida workspace convention).
If no key is found we run in fully canned mode so the demo still lands offline.
"""

from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

# injection-arena/app/config.py -> repo root is three parents up:
#   config.py -> app -> injection-arena -> Hackathons -> Maida.AI
_WORKSPACE_ROOT = Path(__file__).resolve().parents[3]
_ENV_SECRET = _WORKSPACE_ROOT / ".env.secret"

# Only load the shared secret file if the key is not already in the environment.
if not os.environ.get("OPENAI_API_KEY") and _ENV_SECRET.exists():
    load_dotenv(_ENV_SECRET)

# Models offered in the UI selector. First entry is the default.
MODELS = [
    "gpt-4o-mini",
    "gpt-4o",
    "gpt-4.1-mini",
    "gpt-4.1",
    "gpt-5-mini",
]
DEFAULT_MODEL = os.environ.get("ARENA_MODEL", MODELS[0])

# Back-compat alias used by /api/status.
MODEL = DEFAULT_MODEL


def resolve_model(model: str | None) -> str:
    """Only allow models from the curated list; otherwise fall back to default."""
    return model if model in MODELS else DEFAULT_MODEL


def has_openai_key() -> bool:
    """True when a usable OpenAI key is present."""
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    return bool(key) and not key.startswith("sk-demo")


def live_mode() -> bool:
    """Whether the arena should attempt live LLM calls.

    ``ARENA_FORCE_CANNED=1`` forces the deterministic replay path regardless of
    whether a key exists (useful for a guaranteed-to-land stage run).
    """
    if os.environ.get("ARENA_FORCE_CANNED") == "1":
        return False
    return has_openai_key()
