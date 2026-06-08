from __future__ import annotations

import os
from typing import Any

from config import CONFIG


def run_live_anchor(summary: dict[str, Any]) -> dict[str, str]:
    if not os.getenv("OPENAI_API_KEY"):
        return {"status": "mock", "text": "OpenAI key missing; live anchor unavailable."}
    try:
        from openai import OpenAI

        client = OpenAI()
        response = client.chat.completions.create(
            model=CONFIG["persona_model"],
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a concise synthetic customer research judge. "
                        "React to the proposed wedge in two sentences. Do not claim ground truth."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        "Product: Upfirst, an AI virtual receptionist. "
                        f"Current synthetic verdict: {summary}. "
                        "As a trades/HVAC owner, does the flat unlimited emergency-call positioning feel worth testing?"
                    ),
                },
            ],
            max_tokens=120,
            temperature=0.3,
        )
        return {"status": "live", "text": response.choices[0].message.content or ""}
    except Exception as exc:
        return {"status": "error", "text": f"Live anchor failed: {type(exc).__name__}"}
