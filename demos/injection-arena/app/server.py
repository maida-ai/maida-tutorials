"""FastAPI server: serves the single-page arena and streams runs over SSE."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles

from . import config, scenarios
from .arena import Arena, run_arena

_STATIC = Path(__file__).resolve().parent.parent / "static"

app = FastAPI(title="Agent Injection Arena")


@app.get("/api/status")
async def status() -> dict:
    return {"live": config.live_mode(), "model": config.MODEL}


@app.get("/api/config")
async def api_config() -> dict:
    return {
        "live": config.live_mode(),
        "models": config.MODELS,
        "default_model": config.DEFAULT_MODEL,
        "scenarios": [
            {"id": s.id, "name": s.name, "blurb": s.blurb} for s in scenarios.ALL
        ],
    }


@app.get("/run")
async def run(
    gate: str = "off",
    scenario: str = "office",
    model: str | None = None,
    injection: str | None = None,
):
    # An audience-supplied payload (bring-your-own-injection) replaces the
    # scenario's scripted rounds. Trim and cap it so a stray blank or a giant
    # paste can't wedge the run.
    custom = (injection or "").strip()[:2000] or None

    arena = Arena(
        gate_on=(gate == "on"),
        live=config.live_mode(),
        scenario=scenarios.get(scenario),
        model=config.resolve_model(model),
        custom_injection=custom,
    )

    async def event_stream():
        task = asyncio.create_task(run_arena(arena))
        try:
            while True:
                event = await arena.queue.get()
                if event is None:
                    break
                yield f"data: {json.dumps(event)}\n\n"
        finally:
            await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(_STATIC / "index.html")


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
