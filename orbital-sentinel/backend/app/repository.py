from __future__ import annotations
from datetime import datetime
from typing import Any

from .db import get_supabase


def upsert_ingestion_run(source_url: str, retrieved_at: datetime, record_count: int, checksum: str, status: str = "SUCCESS") -> None:
    get_supabase().table("ingestion_runs").insert({
        "source_url": source_url,
        "retrieved_at": retrieved_at.isoformat(),
        "record_count": record_count,
        "checksum_sha256": checksum,
        "status": status,
    }).execute()


def upsert_objects(records: list[Any]) -> None:
    rows = []
    for r in records:
        rows.append({
            "norad_id": r.norad_id,
            "name": r.name,
            "object_type": infer_object_type(r.name),
            "epoch": r.epoch.isoformat() if r.epoch else None,
            "omm_json": r.fields,
            "source_url": r.source_url,
            "retrieved_at": r.retrieved_at.isoformat(),
        })
    if rows:
        get_supabase().table("objects").upsert(rows, on_conflict="norad_id").execute()


def infer_object_type(name: str) -> str:
    upper = name.upper()
    if "DEB" in upper or "DEBRIS" in upper:
        return "DEBRIS"
    if "R/B" in upper or "ROCKET" in upper:
        return "ROCKET_BODY"
    return "PAYLOAD_OR_OTHER"


def insert_event(event_id: str, event: Any) -> None:
    payload = {
        "id": event_id,
        "object_a_norad": event.object_a.norad_id,
        "object_b_norad": event.object_b.norad_id,
        "tca": event.tca.isoformat(),
        "miss_distance_m": event.miss_distance_m,
        "relative_speed_mps": event.relative_speed_mps,
        "screening_risk": event.screening_risk,
        "window_start": event.window_start.isoformat(),
        "window_end": event.window_end.isoformat(),
        "data_retrieved_at": event.data_retrieved_at.isoformat(),
        "algorithm_version": "screen-v1.0",
    }
    get_supabase().table("conjunction_events").upsert(payload, on_conflict="id").execute()


def get_event(event_id: str) -> dict[str, Any] | None:
    result = get_supabase().table("conjunction_events").select("*, object_a:objects!conjunction_events_object_a_norad_fkey(norad_id,name), object_b:objects!conjunction_events_object_b_norad_fkey(norad_id,name)").eq("id", event_id).maybe_single().execute()
    return result.data


def list_events(limit: int = 25) -> list[dict[str, Any]]:
    result = get_supabase().table("conjunction_events").select("*, object_a:objects!conjunction_events_object_a_norad_fkey(norad_id,name), object_b:objects!conjunction_events_object_b_norad_fkey(norad_id,name)").order("tca").limit(limit).execute()
    return result.data or []


def update_event_explanation(event_id: str, explanation: str, model: str) -> None:
    get_supabase().table("conjunction_events").update({"explanation": explanation, "explanation_model": model}).eq("id", event_id).execute()


def get_objects(limit: int = 80) -> list[dict[str, Any]]:
    result = get_supabase().table("objects").select("norad_id,name,epoch,retrieved_at,source_url,object_type,omm_json").order("retrieved_at", desc=True).limit(limit).execute()
    return result.data or []


def upsert_trajectory_cache(rows: list[dict[str, Any]]) -> None:
    if rows:
        get_supabase().table("trajectory_cache").upsert(rows, on_conflict="norad_id,sample_time").execute()


def get_freshness() -> dict[str, Any] | None:
    result = get_supabase().table("ingestion_runs").select("retrieved_at,source_url,record_count,checksum_sha256,status").order("retrieved_at", desc=True).limit(1).maybe_single().execute()
    return result.data
