from engine.factor_model import score_matrix
from engine.loaders import load_groups, load_personas, load_seed, load_variants
from engine.stage4_fitness import aggregate


def test_wedge_gate_trades_hvac_top_and_law_trust_gated():
    seed = load_seed()
    groups = load_groups(seed)
    personas = load_personas(seed)
    variants = load_variants(seed)
    group_ids = [g.id for g in groups]
    by_persona = {p.id: p for p in personas}
    reactions = score_matrix(personas, variants)

    for variant in variants:
        variant.fitness = aggregate(variant, reactions, by_persona, group_ids)

    segment_best = {
        group_id: max(v.fitness.by_segment[group_id]["intent"] for v in variants)
        for group_id in group_ids
    }
    ranked = sorted(segment_best, key=segment_best.get, reverse=True)

    assert set(ranked[:2]) == {"trades", "hvac"}
    law_best = max((v.fitness.by_segment["law"] for v in variants), key=lambda row: row["intent"])
    trades_best = max((v.fitness.by_segment["trades"] for v in variants), key=lambda row: row["intent"])
    assert law_best["value"] > trades_best["value"]
    assert law_best["readiness"] < trades_best["readiness"]
