from __future__ import annotations

import asyncio
import copy
import json
from typing import Any

import jsonpatch

from engine.contracts import empty_graph_state


class Bridge:
    def __init__(self) -> None:
        self.state = empty_graph_state()
        self.q: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
        self.subscribers: set[asyncio.Queue[tuple[str, dict[str, Any]]]] = set()
        self.recorded: list[dict[str, Any]] = []

    def snapshot_payload(self) -> tuple[str, dict[str, Any]]:
        return "STATE_SNAPSHOT", {"snapshot": self.state}

    def subscribe(self) -> asyncio.Queue[tuple[str, dict[str, Any]]]:
        queue: asyncio.Queue[tuple[str, dict[str, Any]]] = asyncio.Queue()
        self.subscribers.add(queue)
        return queue

    def unsubscribe(self, queue: asyncio.Queue[tuple[str, dict[str, Any]]]) -> None:
        self.subscribers.discard(queue)

    async def publish(self, event: str, payload: dict[str, Any]) -> None:
        await self.q.put((event, payload))
        for queue in list(self.subscribers):
            await queue.put((event, payload))

    async def snapshot(self) -> None:
        event, payload = self.snapshot_payload()
        await self.publish(event, payload)

    async def replace_state(self, new_state: dict[str, Any]) -> None:
        self.state = copy.deepcopy(new_state)
        payload = {"snapshot": self.state}
        self.recorded.append({"event": "STATE_SNAPSHOT", "data": payload})
        await self.publish("STATE_SNAPSHOT", payload)

    async def mutate(self, new_state: dict[str, Any], narration: str | None = None) -> None:
        if narration is not None:
            new_state["narration"] = narration
        delta = jsonpatch.make_patch(self.state, new_state).patch
        self.state = copy.deepcopy(new_state)
        payload = {"delta": delta}
        self.recorded.append({"event": "STATE_DELTA", "data": payload})
        await self.publish("STATE_DELTA", payload)

    def replay_delay(self, event: str, data: dict[str, Any]) -> float:
        if event == "STATE_SNAPSHOT":
            phase = data.get("snapshot", {}).get("phase")
            return 1.2 if phase == "curating" else 0.4

        delta = data.get("delta", [])
        paths = {op.get("path"): op for op in delta}
        if any(op.get("op") == "add" and str(op.get("path", "")).startswith("/nodes/p") for op in delta):
            return 1.65
        if any(op.get("op") == "add" and str(op.get("path", "")).startswith("/nodes/v_gen0") for op in delta):
            return 2.4
        if any(op.get("path") == "/phase" and op.get("value") == "reacting" for op in delta):
            return 2.8
        if any(op.get("path") == "/phase" and op.get("value") == "deliberating" for op in delta):
            return 4.2
        if any(op.get("path") == "/phase" and op.get("value") == "evolving" for op in delta):
            return 5.0
        if any(op.get("path") == "/generation" for op in delta):
            return 2.4
        if any(op.get("path") == "/phase" and op.get("value") == "converged" for op in delta):
            return 3.8
        if any(str(op.get("path", "")).startswith("/islands") for op in delta):
            return 2.0
        if paths:
            return 0.9
        return 0.4

    async def replay(self, events: list[dict[str, Any]], delay: float | None = None) -> None:
        self.state = empty_graph_state()
        await self.publish("STATE_SNAPSHOT", {"snapshot": self.state})
        await asyncio.sleep(0.8)
        for item in events:
            event = item["event"]
            data = item["data"]
            if event == "STATE_SNAPSHOT":
                self.state = data["snapshot"]
            elif event == "STATE_DELTA":
                self.state = jsonpatch.apply_patch(self.state, data["delta"], in_place=False)
            await self.publish(event, data)
            await asyncio.sleep(delay if delay is not None else self.replay_delay(event, data))

    def dump_recording(self, path: str) -> None:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.recorded, f, indent=2)
