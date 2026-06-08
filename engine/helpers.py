from __future__ import annotations

import hashlib
import json
import math
from typing import Any


VERT = {
    "trades": "contractors",
    "hvac": "contractors",
    "propmgmt": "property",
    "law": "legal",
    "realestate": "property",
    "finance": "accounting",
}


def sigmoid(x: float) -> float:
    return 1 / (1 + math.exp(-x))


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def vertical_of(group_id: str) -> str:
    return VERT.get(group_id, group_id)


def est_monthly_cost(genes: dict[str, Any], persona: Any) -> float:
    if genes["price_model"] == "flat":
        return float(genes["price_point_usd"])
    if genes["price_model"] == "per_minute":
        return float(genes["price_point_usd"]) * persona.call_volume_per_week * 4.3 * 3.0
    return float(genes["price_point_usd"]) * persona.call_volume_per_week * 4.3


def price_term(genes: dict[str, Any], persona: Any) -> float:
    monthly = est_monthly_cost(genes, persona)
    ceiling = float(persona.price_ceiling_usd_per_mo)
    if monthly <= ceiling:
        return 1.0 - monthly / max(ceiling, 1)
    return -1.5 * (monthly - ceiling) / max(ceiling, 1)


def driver_term(genes: dict[str, Any], persona: Any) -> float:
    want = persona.price_frame
    if want == "reliability" and genes.get("proof") == "testimonial":
        return 0.6
    if want == "price" and genes["price_model"] == "flat":
        return 0.4
    if want == "compliance" and "human" in " ".join(genes.get("bullets", [])).lower():
        return 0.3
    return 0.0


def price_attractiveness(genes: dict[str, Any]) -> float:
    return 0.85 if genes["price_model"] == "flat" else 0.55


def seeded_noise(persona: Any, variant: Any, scale: float) -> float:
    payload = json.dumps([persona.id, variant.id], sort_keys=True)
    h = int(hashlib.sha1(payload.encode("utf-8")).hexdigest()[:8], 16)
    unit = (h % 1000) / 1000.0
    return (unit - 0.5) * 2 * scale


def genes_hash(genes: dict[str, Any]) -> str:
    payload = json.dumps(genes, sort_keys=True)
    return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]
