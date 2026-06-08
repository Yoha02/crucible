from engine.generality import cached_generality_run


def test_product_two_generality_run_surfaces_different_wedge():
    result = cached_generality_run()

    assert result["product"] == "QueueHero"
    assert result["winner"]["segment"] != "trades"
    assert result["winner"]["intent"] > 0.4
    assert "same priors" in result["takeaway"].lower()
