from engine.contracts import empty_graph_state


def test_empty_graph_state_shape():
    state = empty_graph_state()
    assert state["phase"] == "idle"
    assert isinstance(state["nodes"], dict)
    assert state["hud"]["wedge"] is None
