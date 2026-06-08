from __future__ import annotations

from typing import Any


OBJECTION_TAGS = [
    "too_expensive",
    "price_unclear",
    "not_for_my_business",
    "dont_trust_ai",
    "need_human_touch",
    "compliance_risk",
    "already_have_this",
    "caps_too_low",
    "unclear_value",
    "not_painful_enough",
    "sounds_generic",
]

LIKED_TAGS = [
    "speaks_to_my_pain",
    "vertical_fit",
    "right_price",
    "trustworthy_voice",
    "strong_proof",
    "no_caps",
]


def derive_objections(
    genes: dict[str, Any],
    persona: Any,
    *,
    price_fit: float,
    readiness: float,
    vmatch: float,
    value_index: float,
) -> list[str]:
    weighted: list[tuple[float, str]] = []
    if price_fit < 0:
        weighted.append((abs(price_fit) + 0.4, "too_expensive"))
    if genes["price_model"] == "per_call" and persona.call_volume_per_week >= 60:
        weighted.append((0.9, "caps_too_low"))
    if readiness < 0.35:
        weighted.append((1.1 - readiness, "dont_trust_ai"))
    if persona.price_frame == "human_touch":
        weighted.append((0.9, "need_human_touch"))
    if persona.price_frame == "compliance":
        weighted.append((0.85, "compliance_risk"))
    if vmatch < 0:
        weighted.append((0.8, "not_for_my_business"))
    if genes.get("proof") == "none" and persona.skepticism > 0.5:
        weighted.append((0.7 + persona.skepticism * 0.2, "sounds_generic"))
    if value_index < 0.4:
        weighted.append((0.6, "not_painful_enough"))
    if not weighted:
        weighted.append((0.3, "unclear_value"))
    return [tag for _, tag in sorted(weighted, reverse=True)[:2]]


def derive_liked(
    genes: dict[str, Any],
    *,
    price_fit: float,
    readiness: float,
    vmatch: float,
    frame_fit: float,
) -> list[str]:
    weighted: list[tuple[float, str]] = []
    if vmatch > 0:
        weighted.append((0.9, "vertical_fit"))
    if price_fit > 0.5:
        weighted.append((0.8, "right_price"))
    if genes["price_model"] == "flat":
        weighted.append((0.7, "no_caps"))
    if readiness > 0.7:
        weighted.append((0.65, "trustworthy_voice"))
    if frame_fit > 0:
        weighted.append((0.6, "speaks_to_my_pain"))
    if genes.get("proof") in ("testimonial", "stat"):
        weighted.append((0.55, "strong_proof"))
    if not weighted:
        weighted.append((0.2, "speaks_to_my_pain"))
    return [tag for _, tag in sorted(weighted, reverse=True)[:2]]
