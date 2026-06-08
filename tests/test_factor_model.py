from engine.factor_model import score
from engine.helpers import est_monthly_cost, price_term, vertical_of
from engine.loaders import load_personas, load_seed, load_variants


def test_helpers_follow_spec():
    assert vertical_of("trades") == "contractors"
    seed = load_seed()
    persona = load_personas(seed)[0]
    variant = load_variants(seed)[0]
    assert est_monthly_cost(variant.genes, persona) > persona.price_ceiling_usd_per_mo
    assert price_term(variant.genes, persona) < 0


def test_score_returns_fixed_vocab_tags():
    seed = load_seed()
    persona = load_personas(seed)[4]
    variant = load_variants(seed)[0]
    reaction = score(persona, variant)
    assert 0 <= reaction.intent <= 1
    assert reaction.objection_tags
    assert reaction.liked_tags
