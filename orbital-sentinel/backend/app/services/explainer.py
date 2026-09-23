from __future__ import annotations

from openai import OpenAI

from ..config import Settings
from .screening import Conjunction

SYSTEM = """You are ORBITAL SENTINEL's constrained operator-summary generator.
You are NOT an astrodynamics engine. You may only restate and interpret the structured facts supplied to you.
Never invent probability of collision, object size, covariance, maneuverability, observation quality, sensor measurements, or orbital elements.
Never convert a screening tier into a probability or operational warning.
Call the tier exactly a prototype 'Screening Risk' tier.
Keep the explanation under 120 words, plain-language, calm, and factual.
"""


def deterministic_summary(event: Conjunction) -> str:
    return (
        f"{event.object_a.name} and {event.object_b.name} have a screened closest approach at "
        f"{event.tca.isoformat()} UTC. The refined miss distance is {event.miss_distance_m/1000:.3f} km "
        f"with relative speed {event.relative_speed_mps/1000:.3f} km/s. "
        f"Prototype Screening Risk: {event.screening_risk}. This is a geometric screening result, not an operational probability of collision."
    )


def explain_event(event: Conjunction, settings: Settings) -> tuple[str, str]:
    facts = (
        f"Object A: {event.object_a.name} (NORAD {event.object_a.norad_id})\n"
        f"Object B: {event.object_b.name} (NORAD {event.object_b.norad_id})\n"
        f"TCA UTC: {event.tca.isoformat()}\n"
        f"Miss distance: {event.miss_distance_m:.3f} m\n"
        f"Relative speed: {event.relative_speed_mps:.3f} m/s\n"
        f"Prototype Screening Risk: {event.screening_risk}\n"
        f"Orbit data retrieved UTC: {event.data_retrieved_at.isoformat()}\n"
    )
    if not settings.openai_api_key:
        return deterministic_summary(event), "deterministic-fallback"

    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=settings.openai_model,
        instructions=SYSTEM,
        input=f"Summarize these facts for an operator. Do not add any facts.\n\n{facts}",
        max_output_tokens=settings.llm_max_output_tokens,
        store=False,
    )
    text = (response.output_text or "").strip()
    if not text:
        return deterministic_summary(event), "deterministic-fallback"
    return text, settings.openai_model
