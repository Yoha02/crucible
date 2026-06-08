from __future__ import annotations

from collections import defaultdict

from engine.contracts import Fitness, Persona, Reaction, Variant


def aggregate(
    variant: Variant,
    reactions: list[Reaction],
    personas_by_id: dict[str, Persona],
    group_ids: list[str],
) -> Fitness:
    buckets: dict[str, list[Reaction]] = defaultdict(list)
    for reaction in reactions:
        if reaction.variant_id == variant.id:
            buckets[personas_by_id[reaction.persona_id].group_id].append(reaction)

    by_segment: dict[str, dict[str, float]] = {}
    overall_numer = 0.0
    overall_denom = 0.0
    for group_id in group_ids:
        rows = buckets.get(group_id, [])
        if not rows:
            by_segment[group_id] = {"intent": 0.0, "value": 0.0, "readiness": 0.0, "wtp": 0.0}
            continue
        denom = sum(personas_by_id[r.persona_id].weight for r in rows)
        intent = sum(r.intent * personas_by_id[r.persona_id].weight for r in rows) / denom
        value = sum(r.value_index * personas_by_id[r.persona_id].weight for r in rows) / denom
        readiness = sum(r.readiness_index * personas_by_id[r.persona_id].weight for r in rows) / denom
        wtp = sum(r.wtp_usd_per_mo * personas_by_id[r.persona_id].weight for r in rows) / denom
        by_segment[group_id] = {
            "intent": round(intent, 4),
            "value": round(value, 4),
            "readiness": round(readiness, 4),
            "wtp": round(wtp, 2),
        }
        overall_numer += intent * denom
        overall_denom += denom

    return Fitness(
        overall_intent=round(overall_numer / max(overall_denom, 1e-6), 4),
        by_segment=by_segment,
    )


def best_segment(fitness: Fitness) -> str:
    return max(fitness.by_segment.items(), key=lambda row: row[1]["intent"])[0]


def island_summary(variants: list[Variant], group_ids: list[str]) -> dict[str, dict[str, float | str]]:
    islands: dict[str, dict[str, float | str]] = {}
    for group_id in group_ids:
        rows = [
            v.fitness.by_segment[group_id]
            for v in variants
            if v.fitness is not None and v.status == "alive"
        ]
        if not rows:
            islands[group_id] = {"value": 0.0, "readiness": 0.0, "intent_best": 0.0, "status": "active"}
            continue
        best = max(rows, key=lambda r: r["intent"])
        islands[group_id] = {
            "value": round(max(r["value"] for r in rows), 4),
            "readiness": round(max(r["readiness"] for r in rows), 4),
            "intent_best": round(best["intent"], 4),
            "status": "active",
        }
    return islands
