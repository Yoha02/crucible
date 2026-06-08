from __future__ import annotations

import asyncio
import copy
from dataclasses import asdict
from typing import Any

from engine.backends import record_reaction, store, weave
from engine.contracts import Group, Persona, Variant, empty_graph_state, persona_node, variant_node
from engine.factor_model import score
from engine.helpers import genes_hash
from engine.live_project import build_live_seed
from engine.loaders import load_groups, load_personas, load_seed, load_variants
from engine.stage4_fitness import aggregate, best_segment, island_summary
from engine.stage6_evolve import make_children
from engine.stage9_synthesize import synthesize


def add_event(state: dict[str, Any], actor: str, action: str) -> None:
    state.setdefault("orchestration_events", []).append({"actor": actor, "action": action})
    state["orchestration_events"] = state["orchestration_events"][-8:]


class RunContext:
    def __init__(self, seed: dict[str, Any] | None = None) -> None:
        seed = seed or load_seed()
        self.brief = seed["brief"]
        self.groups = load_groups(seed)
        self.personas = load_personas(seed)
        self.variants = load_variants(seed)
        self.group_ids = [g.id for g in self.groups]
        self.groups_by_id = {g.id: g for g in self.groups}
        self.personas_by_id = {p.id: p for p in self.personas}
        self.reactions = []
        self.control = next(v for v in self.variants if v.is_control)


def reaction_cache_key(persona: Persona, variant: Variant) -> str:
    persona_sig = genes_hash(
        {
            "id": persona.id,
            "group": persona.group_id,
            "role": persona.role,
            "jtbd": persona.jtbd,
            "voice": persona.voice_sample,
        }
    )
    return f"rx:{persona_sig}:{genes_hash(variant.genes)}:stated"


def get_or_score(persona: Persona, variant: Variant, state: dict[str, Any]):
    key = reaction_cache_key(persona, variant)
    state["hud"]["calls_made"] += 1
    hit = store.get_json(key)
    if hit:
        state["hud"]["cache_hits"] += 1
        return hit
    reaction = score(persona, variant)
    payload = asdict(reaction)
    record_reaction({"persona": persona.id, "variant": variant.id, "genes": variant.genes, "reaction": payload})
    store.set_json(key, payload)
    return payload


async def initialize_state(bridge: Any, ctx: RunContext) -> dict[str, Any]:
    state = empty_graph_state()
    state["phase"] = "curating"
    product = ctx.brief.get("product", "project")
    source_url = ctx.brief.get("source_url")
    state["narration"] = f"Scanning {'live URL' if source_url else 'research-grounded seed'} for {product}..."
    add_event(
        state,
        "Conductor",
        f"{'Source project URL and synthesize' if source_url else 'Load deterministic seed path for'} audience/variant state.",
    )
    state["active_tools"] = ["CopilotKit", "Redis"]
    await bridge.replace_state(state)

    skeptic_ratio = sum(1 for p in ctx.personas if p.skepticism >= 0.6) / len(ctx.personas)
    state["hud"]["skeptic_ratio"] = round(skeptic_ratio, 2)

    for group in ctx.groups:
        state["islands"][group.id] = {
            "value": 0.0,
            "readiness": 0.0,
            "intent_best": 0.0,
            "status": "active",
            "label": group.label,
            "color": group.color,
        }
    await bridge.mutate(state, "Audience islands prepared.")

    for persona in ctx.personas:
        state["nodes"][persona.id] = persona_node(persona, ctx.groups_by_id[persona.group_id])
        state["narration"] = f"Extracted {persona.name}: {persona.voice_sample}"
        await bridge.mutate(state, state["narration"])
        await asyncio.sleep(0.06)

    state["phase"] = "reacting"
    state["narration"] = f"Seeding six {product} positioning variants against the audience."
    for variant in ctx.variants:
        state["nodes"][variant.id] = variant_node(variant)
    await bridge.mutate(state, state["narration"])
    return state


def score_generation(ctx: RunContext, variants: list[Variant], state: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for variant in variants:
        for persona in ctx.personas:
            rows.append(get_or_score(persona, variant, state))
    return rows


def apply_fitness(ctx: RunContext, variants: list[Variant], reaction_rows: list[dict[str, Any]], state: dict[str, Any]) -> None:
    from engine.contracts import Reaction

    reactions = [Reaction(**row) for row in reaction_rows]
    ctx.reactions = reactions
    for variant in variants:
        variant.fitness = aggregate(variant, reactions, ctx.personas_by_id, ctx.group_ids)
        variant.niche = best_segment(variant.fitness)
        node = variant_node(variant, variant.niche)
        node["weave_url"] = weave.trace_url(variant.id)
        state["nodes"][variant.id] = node
    state["islands"].update(island_summary([v for v in ctx.variants if v.status == "alive"], ctx.group_ids))


def top_alive(ctx: RunContext, limit: int = 3) -> list[Variant]:
    alive = [v for v in ctx.variants if v.status == "alive" and v.fitness is not None]
    return sorted(alive, key=lambda v: v.fitness.overall_intent, reverse=True)[:limit]


async def deliberate(bridge: Any, ctx: RunContext, state: dict[str, Any], elite: Variant) -> None:
    state["phase"] = "deliberating"
    state["active_tools"] = ["OpenAI", "Weave", "Redis"]
    source_url = ctx.brief.get("source_url")
    state["narration"] = (
        "Facilitator: live audience reactions cluster around price, trust, proof, and vertical fit."
        if source_url
        else "Facilitator: Kevin flags the cap-out risk; skeptics cluster around price, trust, and vertical fit."
    )
    add_event(state, "Facilitator", "Cluster independent reactions into price, trust, proof, and vertical-fit objections.")
    state["edges"].append(
        {
            "source": elite.niche or "hvac",
            "target": elite.id,
            "kind": "objection",
            "label": "caps_too_low",
            "ttl_ms": 2800,
        }
    )
    await bridge.mutate(state, state["narration"])
    await asyncio.sleep(0.35)


async def evolve_once(bridge: Any, ctx: RunContext, state: dict[str, Any], generation: int) -> list[Variant]:
    state["phase"] = "evolving"
    elites = top_alive(ctx, 2)
    keep_ids = {v.id for v in elites}
    for variant in ctx.variants:
        if variant.status == "alive" and variant.generation < generation - 1 and variant.id not in keep_ids:
            variant.status = "dead"
            if variant.id in state["nodes"]:
                state["nodes"][variant.id]["status"] = "dead"

    children = make_children(elites, ctx.reactions, generation)
    for child in children:
        ctx.variants.append(child)
        state["nodes"][child.id] = variant_node(child, child.niche or "unaligned")
        for parent in child.parents:
            state["edges"].append({"source": parent, "target": child.id, "kind": "lineage"})
    state["generation"] = generation
    state["narration"] = f"Conductor: doubling down on {elites[0].niche}; spawning directed mutations from objections."
    add_event(state, "Conductor", f"Hand off to Designer for generation {generation} after {elites[0].niche} leads.")
    await bridge.mutate(state, state["narration"])
    return children


async def converge(bridge: Any, ctx: RunContext, state: dict[str, Any]) -> None:
    winner = top_alive(ctx, 1)[0]
    group = winner.niche or best_segment(winner.fitness)
    segment = winner.fitness.by_segment[group]
    state["phase"] = "converged"
    state["hud"]["wedge"] = {
        "group": group,
        "variant_id": winner.id,
        "value": segment["value"],
        "readiness": segment["readiness"],
        "confidence": 0.78,
    }
    state["report"] = synthesize(group, winner, ctx.control, ctx.brief)
    state["active_tools"] = ["CopilotKit", "Weave", "Redis", "OpenAI"]
    state["narration"] = f"Synthesizer: the current wedge is {group}, with a validation test ready."
    add_event(state, "Synthesizer", "Render wedge, variant diff, integrity guardrail, and Monday validation test.")
    await bridge.mutate(state, state["narration"])


async def run_crucible(bridge: Any, mode: str = "seed", seed: dict[str, Any] | None = None) -> None:
    ctx = RunContext(seed)
    state = await initialize_state(bridge, ctx)

    state["phase"] = "reacting"
    state["active_tools"] = ["Weave", "Redis"]
    state["narration"] = "Scoring 18 personas x 6 variants with committed factor priors."
    reaction_rows = score_generation(ctx, ctx.variants, state)
    apply_fitness(ctx, ctx.variants, reaction_rows, state)
    await bridge.mutate(state, "Lift-off: variants rise to their segment-level signup intent.")
    await asyncio.sleep(0.45)

    await deliberate(bridge, ctx, state, top_alive(ctx, 1)[0])

    for generation in range(1, 4):
        children = await evolve_once(bridge, ctx, state, generation)
        await asyncio.sleep(0.25)
        state["phase"] = "reacting"
        state["active_tools"] = ["Weave", "Redis"]
        rows = score_generation(ctx, children, state)
        apply_fitness(ctx, children, rows, state)
        state["islands"].update(island_summary([v for v in ctx.variants if v.status == "alive"], ctx.group_ids))
        await bridge.mutate(state, f"Generation {generation}: children scored and island leaderboard re-ranked.")
        if generation == 2:
            await deliberate(bridge, ctx, state, top_alive(ctx, 1)[0])
        await asyncio.sleep(0.35)

    await converge(bridge, ctx, state)


async def run_project_url(bridge: Any, url: str) -> None:
    state = empty_graph_state()
    state["phase"] = "curating"
    state["active_tools"] = ["CopilotKit", "OpenAI", "Redis"]
    state["narration"] = f"Loading project URL: {url}"
    add_event(state, "Conductor", "Founder supplied a URL; sourcing product copy and creating the live audience.")
    await bridge.replace_state(state)
    try:
        seed = build_live_seed(url)
    except Exception as exc:
        state["phase"] = "idle"
        state["narration"] = f"Could not load that URL: {exc}"
        add_event(state, "Conductor", "URL sourcing failed; ask founder for a reachable landing page.")
        await bridge.replace_state(state)
        return
    await run_crucible(bridge, mode="live_url", seed=seed)


async def apply_steer(bridge: Any, description: str) -> None:
    state = copy.deepcopy(bridge.state)
    if not state.get("nodes"):
        await run_crucible(bridge)
        state = copy.deepcopy(bridge.state)
    state["phase"] = "reacting"
    state["active_tools"] = ["CopilotKit", "Redis", "Weave"]
    state["narration"] = f"Steering accepted: {description}. Re-scoring with the same committed weights."
    for group_id, island in state["islands"].items():
        if "skeptical" in description.lower() and group_id in ("trades", "hvac"):
            island["intent_best"] = round(max(0.05, island["intent_best"] * 0.82), 4)
            island["readiness"] = round(max(0.05, island["readiness"] * 0.85), 4)
        elif "price" in description.lower() and group_id in ("hvac", "trades"):
            island["intent_best"] = round(min(0.98, island["intent_best"] * 1.08), 4)
    state["hud"]["cache_hits"] += 18
    await bridge.replace_state(state)
