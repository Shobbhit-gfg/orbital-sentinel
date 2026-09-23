from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha1
import asyncio

from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .repository import (
    get_event, get_freshness, get_objects, insert_event, list_events,
    update_event_explanation, upsert_ingestion_run, upsert_objects, upsert_trajectory_cache,
)
from .schemas import ExplainResponse, ScreenRequest
from .services.celestrak import fetch_celestrak
from .services.explainer import explain_event
from .services.propagator import make_time_grid, propagate_satellite
from .services.screening import OrbitObject, screen_conjunctions

settings = get_settings()
app = FastAPI(title=settings.app_name, version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    return {"ok": True, "service": settings.app_name, "data_freshness": get_freshness()}


async def ingest_all():
    unique = {}
    for url in settings.celestrak_source_urls:
        records, checksum, retrieved_at = await fetch_celestrak(url, settings.celestrak_timeout_seconds)
        upsert_ingestion_run(url, retrieved_at, len(records), checksum)
        for record in records:
            unique[record.norad_id] = record
    if unique:
        upsert_objects(list(unique.values()))
    return list(unique.values())


def build_orbit_objects(records, max_objects: int) -> list[OrbitObject]:
    # The demo feed is debris-focused. Deterministic sorting makes runs reproducible while
    # ensuring records explicitly marked DEB/DEBRIS are not crowded out by payloads.
    def key(r):
        debris = "DEB" in r.name.upper() or "DEBRIS" in r.name.upper()
        norad = int(r.norad_id) if r.norad_id.isdigit() else r.norad_id
        return (0 if debris else 1, norad)
    chosen = sorted(records, key=key)[:max_objects]
    return [OrbitObject(
        norad_id=r.norad_id, name=r.name, sat=r.sat, epoch=r.epoch,
        retrieved_at=r.retrieved_at, source_url=r.source_url, fields=r.fields,
    ) for r in chosen]


def event_id_for(event) -> str:
    a, b = sorted([event.object_a.norad_id, event.object_b.norad_id])
    key = f"{a}:{b}:{event.tca.isoformat(timespec='seconds')}"
    return sha1(key.encode()).hexdigest()


def cache_trajectories(objects: list[OrbitObject], window_hours: float, step_seconds: int) -> None:
    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=window_hours)
    times = make_time_grid(now, end, step_seconds)
    rows = []
    for obj in objects:
        result = propagate_satellite(obj.sat, times)
        for idx, t in enumerate(result.times):
            if int(result.errors[idx]) != 0:
                continue
            ecef = result.ecef_km[idx] * 1000.0
            geo = result.geodetic[idx]
            rows.append({
                "norad_id": obj.norad_id,
                "sample_time": t.isoformat(),
                "ecef_x_m": float(ecef[0]),
                "ecef_y_m": float(ecef[1]),
                "ecef_z_m": float(ecef[2]),
                "lat_deg": float(geo[0]),
                "lon_deg": float(geo[1]),
                "height_km": float(geo[2]),
                "data_retrieved_at": obj.retrieved_at.isoformat(),
            })
    upsert_trajectory_cache(rows)


@app.post("/api/screen")
async def screen(request: ScreenRequest):
    records = await ingest_all()
    objects = build_orbit_objects(records, request.max_objects)
    if len(objects) < 2:
        raise HTTPException(status_code=503, detail="Not enough valid orbital records returned by CelesTrak")

    broadphase = request.broadphase_distance_km or settings.coarse_broadphase_distance_km
    events = await asyncio.to_thread(
        screen_conjunctions,
        objects,
        request.window_hours,
        request.coarse_step_seconds,
        request.refine_step_seconds,
        broadphase,
        settings,
    )
    # Trajectory cache is for the visualization layer; failure here should not discard the screening result.
    try:
        await asyncio.to_thread(cache_trajectories, objects, request.window_hours, max(30, request.coarse_step_seconds * 2))
    except Exception:
        pass

    saved = 0
    for event in events:
        try:
            insert_event(event_id_for(event), event)
            saved += 1
        except Exception:
            continue

    return {
        "objects_ingested": len(objects),
        "events_found": len(events),
        "events_persisted": saved,
        "coarse_step_seconds": request.coarse_step_seconds,
        "refine_step_seconds": request.refine_step_seconds,
        "broadphase_distance_km": broadphase,
        "screening_only": True,
    }


@app.get("/api/events")
def events(limit: int = Query(default=25, ge=1, le=100)):
    return {"events": list_events(limit)}


@app.get("/api/events/{event_id}")
def event_detail(event_id: str):
    item = get_event(event_id)
    if not item:
        raise HTTPException(status_code=404, detail="Event not found")
    return item


@app.post("/api/events/{event_id}/explain", response_model=ExplainResponse)
def explain(event_id: str):
    item = get_event(event_id)
    if not item:
        raise HTTPException(status_code=404, detail="Event not found")

    class _Obj:
        def __init__(self, d):
            self.norad_id = str(d["norad_id"])
            self.name = str(d["name"])

    class _Event:
        pass

    e = _Event()
    e.object_a = _Obj(item["object_a"])
    e.object_b = _Obj(item["object_b"])
    e.tca = datetime.fromisoformat(item["tca"].replace("Z", "+00:00"))
    e.miss_distance_m = float(item["miss_distance_m"])
    e.relative_speed_mps = float(item["relative_speed_mps"])
    e.screening_risk = item["screening_risk"]
    e.data_retrieved_at = datetime.fromisoformat(item["data_retrieved_at"].replace("Z", "+00:00"))

    text, model = explain_event(e, settings)
    update_event_explanation(event_id, text, model)
    return ExplainResponse(event_id=event_id, explanation=text, source=model)


@app.get("/api/objects")
def objects(window_hours: float = Query(default=3.0, ge=0.25, le=24), step_seconds: int = Query(default=120, ge=30, le=600), limit: int = Query(default=80, ge=1, le=200)):
    rows = get_objects(limit)
    if not rows:
        return {"objects": [], "data_freshness": get_freshness()}

    now = datetime.now(timezone.utc)
    end = now + timedelta(hours=window_hours)
    times = make_time_grid(now, end, step_seconds)
    output = []
    for row in rows:
        # Rebuild Satrec from stored OMM JSON.
        from sgp4.api import Satrec
        from sgp4 import omm
        sat = Satrec()
        try:
            omm.initialize(sat, row["omm_json"])
            result = propagate_satellite(sat, times)
        except Exception:
            continue
        samples = []
        for idx, t in enumerate(result.times):
            if int(result.errors[idx]) != 0:
                continue
            ecef_m = result.ecef_km[idx] * 1000.0
            samples.append({
                "time": t.isoformat(),
                "ecef": [float(x) for x in ecef_m],
                "geodetic": [float(x) for x in result.geodetic[idx]],
            })
        output.append({
            "norad_id": row["norad_id"],
            "name": row["name"],
            "epoch": row["epoch"],
            "retrieved_at": row["retrieved_at"],
            "source_url": row["source_url"],
            "samples": samples,
        })
    return {"objects": output, "data_freshness": get_freshness()}
