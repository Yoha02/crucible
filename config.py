from __future__ import annotations

import os


def load_env_file(path: str = ".env") -> None:
    if not os.path.exists(path):
        return
    with open(path, "r", encoding="utf-8-sig") as f:
        for line in f:
            raw = line.strip()
            if not raw or raw.startswith("#") or "=" not in raw:
                continue
            key, value = raw.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip())


load_env_file()


CONFIG = {
    "islands": 6,
    "island_size": 3,
    "generations": 4,
    "children_per_lineage": 2,
    "elitism_k": 2,
    "factor_weights": {
        "stakes": 1.2,
        "need": 1.0,
        "vertical": 1.1,
        "price": 1.3,
        "frame": 0.6,
        "driver": 0.7,
        "skeptic": 0.8,
    },
    "trust_threshold": 0.5,
    "trust_sharpness": 6.0,
    "convergence_eps": 0.02,
    "delta_coalesce_ms": 33,
    "live_island_only": os.getenv("LIVE_ISLAND_ONLY", "1") == "1",
    "persona_model": os.getenv("PERSONA_MODEL", "gpt-4o-mini"),
    "orchestrator_model": os.getenv("ORCHESTRATOR_MODEL", "gpt-4o"),
    "force_mock": os.getenv("FORCE_MOCK", "1") == "1",
}


DATA_DIR = os.path.join(os.path.dirname(__file__), "data")
