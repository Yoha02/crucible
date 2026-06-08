from __future__ import annotations

import json
import os
from typing import Any

from config import DATA_DIR
from engine.contracts import Group, Persona, Variant


def load_seed(path: str | None = None) -> dict[str, Any]:
    target = path or os.path.join(DATA_DIR, "seed.json")
    with open(target, "r", encoding="utf-8-sig") as f:
        seed = json.load(f)
    for group in seed.get("groups", []):
        group.pop("fit_hypothesis", None)
    return seed


def load_groups(seed: dict[str, Any]) -> list[Group]:
    return [Group(**g) for g in seed["groups"]]


def load_personas(seed: dict[str, Any]) -> list[Persona]:
    return [Persona(**p) for p in seed["personas"]]


def load_variants(seed: dict[str, Any]) -> list[Variant]:
    variants: list[Variant] = []
    for raw in seed["founding_variants"]:
        variants.append(
            Variant(
                id=raw["id"],
                genes=raw["genes"],
                generation=0,
                parents=[],
                is_control=raw.get("is_control", False),
            )
        )
    return variants
