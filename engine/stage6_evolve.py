from __future__ import annotations

import copy
import re
from collections import Counter

from engine.contracts import Reaction, Variant
from engine.stage4_fitness import best_segment


HEADLINES = {
    "trades": "Catch every emergency call. Flat $199, unlimited.",
    "hvac": "Win the no-AC call before another truck does.",
    "propmgmt": "Triage every tenant emergency before it escalates.",
    "realestate": "Answer every buyer lead before the next agent.",
    "law": "Human-backed intake for calls you cannot miss.",
    "finance": "Compliant call capture for seasonal rushes.",
}


def dominant_objections(variant: Variant, reactions: list[Reaction]) -> list[str]:
    tags: Counter[str] = Counter()
    for reaction in reactions:
        if reaction.variant_id == variant.id:
            tags.update(reaction.objection_tags)
    return [tag for tag, _ in tags.most_common(2)] or ["sounds_generic"]


def mutate_variant(parent: Variant, objection: str, generation: int, niche: str, index: int) -> Variant:
    genes = copy.deepcopy(parent.genes)
    if objection in ("too_expensive", "caps_too_low"):
        genes["price_model"] = "flat"
        genes["price_point_usd"] = min(float(genes.get("price_point_usd", 199)), 199.0)
        genes["headline"] = HEADLINES.get(niche, genes["headline"])
        genes["bullets"] = ["Unlimited calls", "Emergency keyword routing", "Never hit a monthly cap"]
    elif objection == "dont_trust_ai":
        genes["proof"] = "testimonial"
        genes["frame"] = "gain"
        genes["subhead"] = "A natural receptionist with clear handoff rules and human backup when needed."
    elif objection == "not_for_my_business":
        genes["vertical_focus"] = niche
        genes["headline"] = HEADLINES.get(niche, genes["headline"])
    elif objection == "need_human_touch":
        genes["proof"] = "testimonial"
        genes["subhead"] = f"AI speed for {niche}, with human backup for sensitive calls."
        genes["bullets"] = list(dict.fromkeys([*genes.get("bullets", []), "Human backup available"]))
    elif objection == "sounds_generic":
        genes["proof"] = "stat"
        genes["vertical_focus"] = niche
        genes["headline"] = HEADLINES.get(niche, genes["headline"])
    elif objection == "not_painful_enough":
        genes["frame"] = "loss"
        genes["headline"] = HEADLINES.get(niche, "Every missed call is a job your competitor just won.")

    safe = re.sub(r"[^a-z0-9]+", "_", objection.lower()).strip("_")
    return Variant(
        id=f"v_gen{generation}_{niche}_{safe}_{index}",
        genes=genes,
        generation=generation,
        parents=[parent.id],
        niche=niche,
    )


def make_children(elites: list[Variant], reactions: list[Reaction], generation: int) -> list[Variant]:
    children: list[Variant] = []
    for index, parent in enumerate(elites):
        niche = best_segment(parent.fitness) if parent.fitness else parent.niche or "trades"
        for objection in dominant_objections(parent, reactions):
            children.append(mutate_variant(parent, objection, generation, niche, len(children)))
    if len(elites) >= 2:
        a, b = elites[0], elites[1]
        niche = best_segment(a.fitness) if a.fitness else "trades"
        genes = copy.deepcopy(a.genes)
        genes["price_model"] = b.genes.get("price_model", genes["price_model"])
        genes["price_point_usd"] = b.genes.get("price_point_usd", genes["price_point_usd"])
        genes["proof"] = b.genes.get("proof", genes["proof"])
        children.append(
            Variant(
                id=f"v_gen{generation}_{niche}_crossover",
                genes=genes,
                generation=generation,
                parents=[a.id, b.id],
                niche=niche,
            )
        )
    return children[:4]
