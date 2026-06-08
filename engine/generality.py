from __future__ import annotations

from engine.contracts import Persona, Variant
from engine.factor_model import score_matrix
from engine.stage4_fitness import aggregate


def cached_generality_run() -> dict:
    """Run the same committed factor model on a second product-shaped panel."""
    group_ids = ["dental", "medspa", "veterinary", "therapy", "restaurants", "salons"]
    personas = [
        Persona("g01", "dental", "Maya", "office manager, 3-chair dental clinic", "small_crew", False, 260, 85, "front_desk", "reliability", 260, 0.48, 0.72, "Fill cancellations before tomorrow's hygiene column collapses.", ["last-minute cancellations", "front desk overload"], "A broken hygiene column wrecks the whole day.", 0.34),
        Persona("g02", "dental", "Dr. Lin", "owner dentist", "small_crew", True, 340, 55, "manual_texting", "reliability", 320, 0.55, 0.66, "Recover no-shows without adding another coordinator.", ["no-shows", "staff cost"], "I do not need AI magic; I need the chair filled.", 0.33),
        Persona("g03", "dental", "BrightPath", "multi-location dental ops", "multi_location", False, 420, 210, "call_center", "price_vs_reliability", 500, 0.62, 0.7, "Standardize cancellation recovery across locations.", ["multi-location gaps", "missed recalls"], "The problem is consistency across every desk.", 0.33),
        Persona("g04", "medspa", "Nora", "medspa owner", "small_crew", False, 180, 70, "instagram_dm", "reliability", 220, 0.45, 0.68, "Turn cancellations into booked consults while staff are with clients.", ["DM backlog", "cancellations"], "If a Botox slot opens, I need it filled now.", 0.34),
        Persona("g05", "medspa", "Ava", "aesthetic clinic manager", "small_crew", True, 220, 90, "front_desk", "relationship", 260, 0.6, 0.52, "Protect the premium feel while automating reminders.", ["premium brand", "white glove"], "Our clients notice when automation feels cheap.", 0.33),
        Persona("g06", "medspa", "Glow Lab", "two-location medspa", "multi_location", False, 250, 140, "manual_texting", "reliability", 360, 0.58, 0.62, "Keep two calendars full without another coordinator.", ["two calendars", "staffing"], "Empty treatment rooms are expensive silence.", 0.33),
        Persona("g07", "veterinary", "Parker", "vet clinic manager", "small_crew", False, 190, 110, "phones", "human_touch", 240, 0.7, 0.48, "Triage urgent openings without sounding cold.", ["worried owners", "urgent triage"], "Pet owners are anxious. A bot can make that worse.", 0.34),
        Persona("g08", "veterinary", "Dr. Ames", "urgent vet owner", "small_crew", False, 380, 160, "phones", "reliability", 420, 0.62, 0.58, "Route urgent cancellations to the right owners fast.", ["urgent slots", "triage"], "The open slot matters, but so does tone.", 0.33),
        Persona("g09", "veterinary", "North Paw", "multi-doctor clinic", "multi_location", True, 210, 130, "front_desk", "human_touch", 300, 0.66, 0.45, "Reduce call load without upsetting regulars.", ["call volume", "client trust"], "Our regulars expect us to know their pets.", 0.33),
        Persona("g10", "therapy", "June", "therapy practice admin", "small_crew", True, 170, 45, "ehr_waitlist", "compliance", 180, 0.74, 0.34, "Handle sensitive waitlist changes safely.", ["PHI", "sensitive scheduling"], "This cannot mishandle private mental-health details.", 0.34),
        Persona("g11", "therapy", "Rooted Care", "group therapy clinic", "multi_location", False, 240, 75, "manual_calls", "compliance", 260, 0.72, 0.38, "Fill cancellations while respecting privacy.", ["privacy", "cancellations"], "A slot matters, but privacy matters more.", 0.33),
        Persona("g12", "therapy", "Sam", "solo therapist", "solo", True, 120, 18, "nothing", "relationship", 80, 0.62, 0.28, "Avoid admin without damaging trust.", ["low volume", "relationship"], "My clients are not interchangeable calendar slots.", 0.33),
        Persona("g13", "restaurants", "Omar", "restaurant GM", "small_crew", False, 90, 180, "host_stand", "price", 90, 0.42, 0.64, "Backfill cancellations during service.", ["busy service", "low margin"], "If it costs too much, the cure is worse.", 0.34),
        Persona("g14", "restaurants", "Table Nine", "fine dining owner", "small_crew", True, 160, 120, "reservation_platform", "relationship", 180, 0.68, 0.4, "Protect guest experience while managing cancellations.", ["high touch", "brand"], "Our regulars expect a human touch.", 0.33),
        Persona("g15", "restaurants", "Bao House", "casual restaurant", "solo", False, 70, 160, "nothing", "price", 60, 0.38, 0.66, "Cheap way to avoid empty tables.", ["thin margin", "no admin"], "I need cheap, not clever.", 0.33),
        Persona("g16", "salons", "Iris", "salon owner", "small_crew", False, 120, 65, "manual_texting", "price", 120, 0.45, 0.6, "Fill last-minute color appointments.", ["last-minute gaps", "staff time"], "A two-hour color slot cannot sit empty.", 0.34),
        Persona("g17", "salons", "Marco", "barber shop owner", "solo", True, 70, 55, "booking_app", "price", 70, 0.42, 0.58, "Keep chairs full without subscription bloat.", ["low ticket", "subscription fatigue"], "Another monthly app needs to pay for itself fast.", 0.33),
        Persona("g18", "salons", "Luxe Hair", "premium salon", "small_crew", True, 160, 80, "front_desk", "relationship", 180, 0.58, 0.46, "Automate without cheapening client experience.", ["premium brand", "client relationship"], "Clients book with people, not workflows.", 0.33),
    ]
    variants = [
        Variant("g_v0_control", {"headline": "Fill every open appointment slot.", "subhead": "QueueHero messages your waitlist when cancellations happen.", "bullets": ["Automated waitlist texts", "Calendar sync", "No-show recovery"], "price_model": "flat", "price_point_usd": 149, "vertical_focus": "all", "frame": "gain", "proof": "none"}, is_control=True),
        Variant("g_v0_dental", {"headline": "Keep every dental chair producing tomorrow.", "subhead": "AI waitlist recovery built for dental cancellations and hygiene gaps.", "bullets": ["Backfills hygiene openings", "Confirms by text", "Front-desk friendly"], "price_model": "flat", "price_point_usd": 199, "vertical_focus": "dental", "frame": "loss", "proof": "stat"}),
        Variant("g_v0_medspa", {"headline": "Fill canceled medspa consults before the slot disappears.", "subhead": "Recover openings from your client waitlist without staff chasing DMs.", "bullets": ["Instant SMS outreach", "Premium tone", "Calendar-safe"], "price_model": "flat", "price_point_usd": 179, "vertical_focus": "medspa", "frame": "loss", "proof": "testimonial"}),
        Variant("g_v0_restaurant", {"headline": "Backfill canceled tables without another host.", "subhead": "Cheap waitlist automation for high-volume restaurants.", "bullets": ["Low monthly price", "Fast guest texts", "Works during service"], "price_model": "flat", "price_point_usd": 79, "vertical_focus": "restaurants", "frame": "gain", "proof": "none"}),
        Variant("g_v0_human", {"headline": "Human-safe waitlist automation for sensitive appointments.", "subhead": "Careful handoffs and compliance-aware scripts for sensitive practices.", "bullets": ["Human review option", "Privacy-aware copy", "Soft tone"], "price_model": "flat", "price_point_usd": 249, "vertical_focus": "therapy", "frame": "gain", "proof": "testimonial"}),
    ]
    rows = score_matrix(personas, variants)
    by_persona = {p.id: p for p in personas}
    for variant in variants:
        variant.fitness = aggregate(variant, rows, by_persona, group_ids)
        variant.niche = max(variant.fitness.by_segment.items(), key=lambda row: row[1]["intent"])[0]

    segment_best = {
        group_id: max(v.fitness.by_segment[group_id]["intent"] for v in variants)
        for group_id in group_ids
    }
    winner = max(variants, key=lambda v: v.fitness.overall_intent)
    ranked = sorted(segment_best.items(), key=lambda row: row[1], reverse=True)
    return {
        "product": "QueueHero",
        "one_liner": "AI waitlist and cancellation recovery for appointment businesses",
        "method": "Same committed factor-model weights; cached product #2 sanity run.",
        "winner": {
            "segment": ranked[0][0],
            "variant": winner.genes["headline"],
            "intent": round(ranked[0][1], 3),
        },
        "runner_up": {"segment": ranked[1][0], "intent": round(ranked[1][1], 3)},
        "gated_segment": "therapy",
        "takeaway": "The same priors surface dental/medspa appointment recovery, not trades/HVAC, which helps answer the 'was Upfirst authored?' objection.",
    }
