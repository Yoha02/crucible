from __future__ import annotations

import json
import os
from typing import Any, Callable

from config import CONFIG


class MockWeave:
    def __init__(self) -> None:
        self.project = "crucible"

    def init(self, project: str) -> None:
        self.project = project

    def op(self, fn: Callable | None = None) -> Callable:
        def decorator(inner: Callable) -> Callable:
            return inner

        return decorator(fn) if fn else decorator

    def trace_url(self, node_id: str) -> str:
        return f"mock://weave/crucible/{node_id}"


class RealWeave:
    def __init__(self) -> None:
        import weave as weave_lib

        self._weave = weave_lib
        try:
            self._weave.init(os.getenv("WANDB_PROJECT", "crucible"))
        except Exception as exc:
            message = str(exc)
            if "Duplicate entry" not in message and "already exists" not in message:
                raise

    def init(self, project: str) -> None:
        self._weave.init(project)

    def op(self, fn: Callable | None = None) -> Callable:
        return self._weave.op(fn) if fn else self._weave.op()

    def trace_url(self, node_id: str) -> str:
        return os.getenv("WANDB_PROJECT_URL", f"https://wandb.ai/home/weave?project=crucible&node={node_id}")


class MemoryStore:
    def __init__(self) -> None:
        self.cache: dict[str, str] = {}
        self.state: dict[str, Any] = {}

    def get_json(self, key: str) -> Any | None:
        if key not in self.cache:
            return None
        return json.loads(self.cache[key])

    def set_json(self, key: str, value: Any) -> None:
        self.cache[key] = json.dumps(value)

    def cache_size(self) -> int:
        return len(self.cache)


class RedisStore(MemoryStore):
    def __init__(self) -> None:
        super().__init__()
        import redis

        self.redis = redis.from_url(os.environ["REDIS_URL"])
        self.redis.ping()

    def get_json(self, key: str) -> Any | None:
        value = self.redis.get(key)
        if value is None:
            return None
        if isinstance(value, bytes):
            value = value.decode("utf-8")
        return json.loads(value)

    def set_json(self, key: str, value: Any) -> None:
        self.redis.set(key, json.dumps(value))


def make_weave() -> MockWeave | RealWeave:
    if CONFIG["force_mock"] or not os.getenv("WANDB_API_KEY"):
        return MockWeave()
    try:
        return RealWeave()
    except Exception:
        return MockWeave()


def make_store() -> MemoryStore:
    if CONFIG["force_mock"] or not os.getenv("REDIS_URL"):
        return MemoryStore()
    try:
        return RedisStore()
    except Exception:
        return MemoryStore()


weave = make_weave()
store = make_store()


@weave.op
def record_reaction(payload: dict[str, Any]) -> dict[str, Any]:
    return payload
