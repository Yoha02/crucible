from __future__ import annotations

import html
import re
from dataclasses import asdict
from typing import Any
from urllib.parse import urlparse

import requests

from engine.contracts import Group, Persona, Variant


GROUP_TEMPLATES = [
    ("operators", "Operations Owners", "operations", "#E4572E", "reliability"),
    ("sales", "Revenue Teams", "sales", "#F3A712", "speed"),
    ("support", "Support Leaders", "support", "#669BBC", "trust"),
    ("finance", "Finance Buyers", "finance", "#3D348B", "compliance"),
    ("founders", "Founder / Solo Operators", "founders", "#06A77D", "price"),
    ("enterprise", "Enterprise Admins", "enterprise", "#7A6C5D", "human_touch"),
]

PAIN_KEYWORDS = {
    "automation": ["manual work", "repetitive tasks", "handoffs"],
    "ai": ["AI trust", "quality variance", "control"],
    "sales": ["slow follow-up", "lost leads", "pipeline gaps"],
    "support": ["ticket backlog", "response time", "customer trust"],
    "analytics": ["unclear ROI", "reporting gaps", "slow decisions"],
    "security": ["risk", "compliance", "approval"],
    "scheduling": ["missed bookings", "calendar gaps", "admin load"],
    "workflow": ["tool sprawl", "manual coordination", "context switching"],
}


def clean_text(value: str) -> str:
    value = re.sub(r"<(script|style).*?</\1>", " ", value, flags=re.I | re.S)
    value = re.sub(r"<[^>]+>", " ", value)
    value = html.unescape(value)
    return re.sub(r"\s+", " ", value).strip()


def meta_content(markup: str, key: str) -> str | None:
    pattern = rf'<meta[^>]+(?:name|property)=["\']{re.escape(key)}["\'][^>]+content=["\']([^"\']+)["\']'
    match = re.search(pattern, markup, flags=re.I)
    return html.unescape(match.group(1)).strip() if match else None


def fetch_project_page(url: str) -> dict[str, str]:
    parsed = urlparse(url if "://" in url else f"https://{url}")
    target = parsed.geturl()
    response = requests.get(
        target,
        headers={"User-Agent": "CrucibleHackathonBot/0.1"},
        timeout=12,
    )
    response.raise_for_status()
    markup = response.text[:500_000]
    title_match = re.search(r"<title[^>]*>(.*?)</title>", markup, flags=re.I | re.S)
    title = clean_text(title_match.group(1)) if title_match else parsed.netloc
    description = (
        meta_content(markup, "description")
        or meta_content(markup, "og:description")
        or meta_content(markup, "twitter:description")
        or ""
    )
    headline = meta_content(markup, "og:title") or title
    text = clean_text(markup)
    return {
        "url": target,
        "domain": parsed.netloc.replace("www.", ""),
        "title": title,
        "headline": headline,
        "description": description,
        "text": text[:6000],
    }


def infer_product(page: dict[str, str]) -> dict[str, Any]:
    title = page["title"].split("|")[0].split("-")[0].strip() or page["domain"].split(".")[0].title()
    description = page["description"] or page["text"][:220]
    haystack = f"{page['headline']} {description} {page['text'][:1500]}".lower()
    matched = [key for key in PAIN_KEYWORDS if key in haystack]
    pain_terms = []
    for key in matched[:3]:
      pain_terms.extend(PAIN_KEYWORDS[key])
    if not pain_terms:
        pain_terms = ["manual work", "slow response", "unclear ROI"]
    return {
        "product": title[:42],
        "one_liner": description[:220] or f"{title} product positioning from {page['domain']}",
        "pain_terms": list(dict.fromkeys(pain_terms))[:5],
        "domain": page["domain"],
        "artifact": {
            "headline": page["headline"][:84] or title,
            "subhead": description[:180] or f"Positioning extracted from {page['domain']}.",
            "bullets": list(dict.fromkeys(pain_terms))[:3],
            "price_model": "flat",
            "price_point_usd": 149.0,
            "price_note": "estimated from live page; founder should verify",
        },
    }


def make_groups(product: dict[str, Any]) -> list[Group]:
    groups = []
    for index, (group_id, label, vertical, color, driver) in enumerate(GROUP_TEMPLATES):
        groups.append(
            Group(
                id=group_id,
                label=label,
                vertical=vertical,
                market_weight=round(0.22 - index * 0.018, 3),
                economics={
                    "avg_job_value_usd": 900 + index * 520,
                    "missed_call_ev_usd": 180 + index * 55,
                    "pct_calls_unanswered": round(0.48 - index * 0.035, 3),
                    "typical_current_tool": "spreadsheet" if index < 3 else "incumbent_suite",
                },
                why_cant_answer=f"team is stuck with {product['pain_terms'][index % len(product['pain_terms'])]}",
                decision_driver=driver,
                color=color,
            )
        )
    return groups


def make_personas(product: dict[str, Any], groups: list[Group]) -> list[Persona]:
    personas: list[Persona] = []
    shapes = ["solo", "small_crew", "multi_location"]
    names = ["Alex", "Morgan", "Riley", "Jordan", "Casey", "Taylor", "Sam", "Avery", "Quinn"]
    idx = 0
    for group in groups:
        for slot in range(3):
            pain = product["pain_terms"][(idx + slot) % len(product["pain_terms"])]
            skeptical = slot == 2 or group.id in {"finance", "enterprise"}
            personas.append(
                Persona(
                    id=f"live_p{idx + 1:02d}",
                    group_id=group.id,
                    name=f"{names[idx % len(names)]} {group.label.split()[0]}",
                    role=f"{group.label.lower()} buyer",
                    business_shape=shapes[slot],
                    can_answer=slot == 2,
                    cost_per_missed_call_usd=group.economics["missed_call_ev_usd"] + slot * 65,
                    call_volume_per_week=35 + slot * 45 + idx,
                    current_tool=group.economics["typical_current_tool"],
                    price_frame=group.decision_driver,
                    price_ceiling_usd_per_mo=140 + slot * 90 + int(group.market_weight * 500),
                    skepticism=0.72 if skeptical else 0.42 + slot * 0.08,
                    ai_trust=0.36 if group.id in {"finance", "enterprise"} else 0.68 - slot * 0.08,
                    jtbd=f"Reduce {pain} without adding another operational burden.",
                    pain_triggers=[pain, "busy team", "hard to prove ROI"],
                    voice_sample=f"If {product['product']} cannot clearly solve {pain}, I will stay with what we have.",
                    weight=[0.34, 0.33, 0.33][slot],
                )
            )
            idx += 1
    return personas


def make_variants(product: dict[str, Any], groups: list[Group]) -> list[Variant]:
    artifact = product["artifact"]
    focus_a, focus_b, focus_c = groups[0].id, groups[1].id, groups[2].id
    base = {
        "headline": artifact["headline"],
        "subhead": artifact["subhead"],
        "bullets": artifact["bullets"],
        "price_model": artifact["price_model"],
        "price_point_usd": artifact["price_point_usd"],
        "vertical_focus": "all",
        "frame": "gain",
        "proof": "none",
    }
    raw = [
        ("live_v_gen0_control", base, True),
        (
            "live_v_gen0_loss",
            {**base, "headline": f"Stop losing deals to {product['pain_terms'][0]}.", "frame": "loss", "proof": "stat"},
            False,
        ),
        (
            "live_v_gen0_operator",
            {**base, "headline": f"{product['product']} for {groups[0].label}.", "vertical_focus": focus_a, "proof": "testimonial"},
            False,
        ),
        (
            "live_v_gen0_sales",
            {**base, "headline": f"Turn {product['pain_terms'][1]} into booked pipeline.", "vertical_focus": focus_b, "price_point_usd": 199.0},
            False,
        ),
        (
            "live_v_gen0_trust",
            {**base, "headline": "Automation with human control where it matters.", "vertical_focus": focus_c, "proof": "testimonial"},
            False,
        ),
        (
            "live_v_gen0_price",
            {**base, "headline": f"Prove {product['product']} in one week.", "price_point_usd": 79.0, "proof": "none"},
            False,
        ),
    ]
    return [Variant(id=variant_id, genes=genes, is_control=is_control) for variant_id, genes, is_control in raw]


def build_live_seed(url: str) -> dict[str, Any]:
    page = fetch_project_page(url)
    product = infer_product(page)
    groups = make_groups(product)
    personas = make_personas(product, groups)
    variants = make_variants(product, groups)
    return {
        "brief": {
            "product": product["product"],
            "one_liner": product["one_liner"],
            "source_url": page["url"],
            "artifact": product["artifact"],
            "stated_target": "unknown; inferred from live page",
            "stated_verticals": [g.vertical for g in groups],
            "optimize_for": ["signup_intent", "willingness_to_pay"],
        },
        "groups": [asdict(group) for group in groups],
        "personas": [asdict(persona) for persona in personas],
        "founding_variants": [{"id": variant.id, "is_control": variant.is_control, "genes": variant.genes} for variant in variants],
        "source": page,
    }
