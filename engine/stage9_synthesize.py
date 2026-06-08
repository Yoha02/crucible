from __future__ import annotations

from typing import Any

from engine.contracts import Variant
from engine.generality import cached_generality_run


def synthesize(wedge_group: str, winner: Variant, control: Variant, brief: dict[str, Any] | None = None) -> dict:
    brief = brief or {}
    product = brief.get("product", "Upfirst")
    source_url = brief.get("source_url")
    if source_url:
        return {
            "title": f"Wedge found: {wedge_group}",
            "wedge_group": wedge_group,
            "summary": (
                f"{product} appears most winnable with {wedge_group}: this audience combines visible pain, "
                "enough readiness to try a new workflow, and objections that can be answered by sharper positioning."
            ),
            "segment_verdict": [
                {"segment": wedge_group, "verdict": "Beachhead. Highest live-eval intent under the current priors."},
                {"segment": "Adjacent operators", "verdict": "Explore after the beachhead test."},
                {"segment": "Compliance-heavy buyers", "verdict": "Gated by trust and approval risk."},
            ],
            "diff": [
                {"field": "Headline", "before": control.genes["headline"], "after": winner.genes["headline"]},
                {
                    "field": "Price",
                    "before": f"{control.genes['price_point_usd']} {control.genes['price_model']}",
                    "after": f"{winner.genes['price_point_usd']} {winner.genes['price_model']}",
                },
                {"field": "Focus", "before": control.genes["vertical_focus"], "after": winner.genes["vertical_focus"]},
                {"field": "Frame", "before": control.genes["frame"], "after": winner.genes["frame"]},
            ],
            "test": {
                "name": "Monday validation test",
                "instruction": f"Send 25 targeted messages to {wedge_group} buyers using the winning headline.",
                "bar": "Pass if more than 35% reply or click through. Fail fast below 15%.",
                "cost": "$20-75 and one afternoon",
            },
            "integrity": {
                "framing": "Live URL mode is a directional hypothesis engine, not market truth.",
                "fallback": "Demo mode remains available for the rehearsed, deterministic Upfirst path.",
                "lead_claim": "AG-UI state drives a dynamic graph while the founder supplies a live project URL.",
            },
        }
    return {
        "title": "Wedge found: trades + HVAC beachhead",
        "wedge_group": wedge_group,
        "summary": (
            "Law firms score highest on raw value, but they are trust- and compliance-gated. "
            "The winnable entry point is trades/HVAC: high missed-call stakes, high AI readiness, "
            "and owners who physically cannot answer while working."
        ),
        "segment_verdict": [
            {"segment": "Trades / HVAC", "verdict": "Beachhead. High value and high readiness."},
            {"segment": "Law", "verdict": "High value, gated. Revisit after a human-touch story."},
            {"segment": "Real estate / property management", "verdict": "Secondary. Moderate fit."},
            {"segment": "Finance", "verdict": "Deprioritize. Low urgency and low readiness."},
        ],
        "diff": [
            {"field": "Headline", "before": control.genes["headline"], "after": winner.genes["headline"]},
            {
                "field": "Price",
                "before": f"{control.genes['price_point_usd']} {control.genes['price_model']}",
                "after": f"{winner.genes['price_point_usd']} {winner.genes['price_model']}",
            },
            {"field": "Focus", "before": control.genes["vertical_focus"], "after": winner.genes["vertical_focus"]},
            {"field": "Frame", "before": control.genes["frame"], "after": winner.genes["frame"]},
        ],
        "test": {
            "name": "Monday validation test",
            "instruction": "Send 25 cold DMs to independent trades/HVAC operators with the new page.",
            "bar": "Pass if more than 40% reply-to-demo. Fail fast below 20%.",
            "cost": "$20-50 and one afternoon",
        },
        "generality": cached_generality_run(),
        "integrity": {
            "framing": "Directional hypothesis engine, not ground truth.",
            "fallback": "Replay is labeled as replay; Live Anchor is the bounded real-time truth check.",
            "lead_claim": "Best Use of CopilotKit: graph bound to agent state plus live steering.",
        },
    }
