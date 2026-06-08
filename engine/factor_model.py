from __future__ import annotations

from typing import Any

from config import CONFIG
from engine.contracts import Persona, Reaction, Variant
from engine.helpers import (
    clamp,
    driver_term,
    price_attractiveness,
    price_term,
    seeded_noise,
    sigmoid,
    vertical_of,
)
from engine.tags import derive_liked, derive_objections


def score(persona: Persona, variant: Variant) -> Reaction:
    weights = CONFIG["factor_weights"]
    genes = variant.genes

    stakes = persona.cost_per_missed_call_usd / 600.0
    need = 1.0 if not persona.can_answer else 0.3
    value_logit = weights["stakes"] * stakes + weights["need"] * need

    focus = genes["vertical_focus"]
    if focus == "all":
        vmatch = 0.0
    else:
        vmatch = 1.0 if vertical_of(persona.group_id) == focus else -1.0

    pfit = price_term(genes, persona)
    frame_fit = 0.5 if genes["frame"] == "loss" and stakes > 0.6 else 0.0
    dfit = driver_term(genes, persona)
    generic_penalty = persona.skepticism * (0.5 if genes["proof"] == "none" else 0.0)
    fit_logit = (
        weights["vertical"] * vmatch
        + weights["price"] * pfit
        + weights["frame"] * frame_fit
        + weights["driver"] * dfit
        - weights["skeptic"] * generic_penalty
    )

    readiness = sigmoid(CONFIG["trust_sharpness"] * (persona.ai_trust - CONFIG["trust_threshold"]))
    if persona.price_frame == "compliance":
        readiness *= 0.7
    if persona.price_frame == "human_touch":
        readiness *= 0.6

    value_index = sigmoid(value_logit)
    raw_attract = sigmoid(value_logit + fit_logit)
    intent = clamp(readiness * raw_attract + seeded_noise(persona, variant, 0.05))
    wtp = persona.price_ceiling_usd_per_mo * clamp(intent * price_attractiveness(genes))
    sentiment = clamp((intent - 0.5) * 2, -1.0, 1.0)

    objections = derive_objections(
        genes,
        persona,
        price_fit=pfit,
        readiness=readiness,
        vmatch=vmatch,
        value_index=value_index,
    )
    liked = derive_liked(
        genes,
        price_fit=pfit,
        readiness=readiness,
        vmatch=vmatch,
        frame_fit=frame_fit,
    )

    return Reaction(
        persona_id=persona.id,
        variant_id=variant.id,
        generation=variant.generation,
        intent=intent,
        wtp_usd_per_mo=wtp,
        value_index=value_index,
        readiness_index=readiness,
        sentiment=sentiment,
        objection_tags=objections,
        liked_tags=liked,
        verbatim=reaction_copy(persona, variant, objections, liked, intent),
    )


def reaction_copy(
    persona: Persona,
    variant: Variant,
    objections: list[str],
    liked: list[str],
    intent: float,
) -> str:
    if intent >= 0.65:
        return f"{persona.name}: This speaks to me. {liked[0].replace('_', ' ')} matters more than another generic receptionist pitch."
    return f"{persona.name}: I hesitate because of {objections[0].replace('_', ' ')}. {persona.voice_sample}"


def score_matrix(personas: list[Persona], variants: list[Variant]) -> list[Reaction]:
    return [score(persona, variant) for variant in variants for persona in personas]
