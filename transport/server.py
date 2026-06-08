from __future__ import annotations

import asyncio
import json
import os
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from config import DATA_DIR
from engine.simulation import apply_steer, run_crucible, run_project_url
from engine.live_anchor import run_live_anchor
from transport.bridge import Bridge


app = FastAPI(title="Crucible")
bridge = Bridge()
running_task: asyncio.Task | None = None

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class SteerRequest(BaseModel):
    description: str


class ProjectUrlRequest(BaseModel):
    url: str


async def cancel_running_task() -> None:
    global running_task
    if running_task and not running_task.done():
        running_task.cancel()
        try:
            await running_task
        except asyncio.CancelledError:
            pass
    running_task = None


@app.get("/health")
async def health() -> dict[str, str]:
    return {"ok": "true"}


@app.get("/state")
async def state() -> dict[str, Any]:
    return bridge.state


@app.get("/agui")
async def agui() -> EventSourceResponse:
    async def gen():
        event, payload = bridge.snapshot_payload()
        yield {"event": event, "data": json.dumps(payload)}
        queue = bridge.subscribe()
        try:
            while True:
                event, payload = await queue.get()
                yield {"event": event, "data": json.dumps(payload)}
        finally:
            bridge.unsubscribe(queue)

    return EventSourceResponse(gen())


@app.post("/run")
async def run(mode: str = "seed") -> dict[str, Any]:
    global running_task
    if running_task and not running_task.done():
        return {"ok": True, "status": "already_running"}
    running_task = asyncio.create_task(run_crucible(bridge, mode=mode))
    return {"ok": True, "status": "started"}


@app.post("/project-url")
async def project_url(req: ProjectUrlRequest) -> dict[str, Any]:
    global running_task
    await cancel_running_task()
    running_task = asyncio.create_task(run_project_url(bridge, req.url))
    return {"ok": True, "status": "started"}


@app.post("/steer")
async def steer(req: SteerRequest) -> dict[str, bool]:
    await apply_steer(bridge, req.description)
    return {"ok": True}


@app.post("/replay")
async def replay() -> dict[str, bool]:
    global running_task
    path = os.path.join(DATA_DIR, "recorded_run.json")
    if not os.path.exists(path):
        return {"ok": False}
    with open(path, "r", encoding="utf-8") as f:
        events = json.load(f)
    await cancel_running_task()
    running_task = asyncio.create_task(bridge.replay(events))
    return {"ok": True}


@app.post("/live-anchor")
async def live_anchor() -> dict[str, Any]:
    summary = bridge.state.get("hud", {}).get("wedge") or {}
    result = run_live_anchor(summary)
    state = dict(bridge.state)
    state.setdefault("hud", {}).setdefault("calls_made", 0)
    state["hud"]["calls_made"] += 1
    state["active_tools"] = ["OpenAI", "Weave"]
    state["narration"] = f"Live anchor ({result['status']}): {result['text']}"
    await bridge.replace_state(state)
    return {"ok": True, **result}


@app.get("/node/{node_id}")
async def node(node_id: str) -> dict[str, Any]:
    return bridge.state.get("nodes", {}).get(node_id, {})
