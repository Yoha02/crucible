from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Group:
    id: str
    label: str
    vertical: str
    market_weight: float
    economics: dict[str, Any]
    why_cant_answer: str
    decision_driver: str
    color: str


@dataclass
class Persona:
    id: str
    group_id: str
    name: str
    role: str
    business_shape: str
    can_answer: bool
    cost_per_missed_call_usd: float
    call_volume_per_week: int
    current_tool: str
    price_frame: str
    price_ceiling_usd_per_mo: float
    skepticism: float
    ai_trust: float
    jtbd: str
    pain_triggers: list[str]
    voice_sample: str
    weight: float
    embedding: list[float] = field(default_factory=list)
    reactions: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class Fitness:
    overall_intent: float
    by_segment: dict[str, dict[str, float]]


@dataclass
class Variant:
    id: str
    genes: dict[str, Any]
    generation: int = 0
    parents: list[str] = field(default_factory=list)
    niche: str | None = None
    is_control: bool = False
    fitness: Fitness | None = None
    status: str = "alive"


@dataclass
class Reaction:
    persona_id: str
    variant_id: str
    generation: int
    exposure_mode: str = "stated"
    intent: float = 0.0
    wtp_usd_per_mo: float = 0.0
    value_index: float = 0.0
    readiness_index: float = 0.0
    sentiment: float = 0.0
    objection_tags: list[str] = field(default_factory=list)
    liked_tags: list[str] = field(default_factory=list)
    verbatim: str = ""
    confidence: float = 1.0


def dataclass_dict(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return asdict(value)
    return value


def empty_graph_state() -> dict[str, Any]:
    return {
        "run_id": "r1",
        "phase": "idle",
        "generation": 0,
        "islands": {},
        "nodes": {},
        "edges": [],
        "hud": {
            "calls_made": 0,
            "cache_hits": 0,
            "skeptic_ratio": 0.0,
            "wedge": None,
        },
        "narration": "Load the Upfirst demo to begin.",
        "orchestration_events": [],
        "report": None,
        "active_tools": [],
    }


def persona_node(persona: Persona, group: Group) -> dict[str, Any]:
    return {
        "id": persona.id,
        "type": "persona",
        "group": persona.group_id,
        "generation": None,
        "fitness": None,
        "status": "alive",
        "label": persona.name,
        "preview": persona.voice_sample,
        "parents": [],
        "genes": {},
        "color": group.color,
        "role": persona.role,
        "jtbd": persona.jtbd,
    }


def variant_node(variant: Variant, group: str = "unaligned") -> dict[str, Any]:
    return {
        "id": variant.id,
        "type": "variant",
        "group": group,
        "generation": variant.generation,
        "fitness": 0.0 if variant.fitness is None else variant.fitness.overall_intent,
        "status": variant.status,
        "label": variant.genes.get("headline", variant.id),
        "preview": variant.genes.get("subhead", ""),
        "parents": variant.parents,
        "genes": variant.genes,
        "is_control": variant.is_control,
        "niche": variant.niche,
        "fitness_detail": None if variant.fitness is None else dataclass_dict(variant.fitness),
    }
