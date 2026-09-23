from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import itertools
import numpy as np
from scipy.spatial import cKDTree

from sgp4.api import Satrec

from ..config import Settings
from .propagator import propagate_satellite, make_time_grid


@dataclass
class OrbitObject:
    norad_id: str
    name: str
    sat: Satrec
    epoch: datetime | None
    retrieved_at: datetime
    source_url: str
    fields: dict


@dataclass
class Conjunction:
    object_a: OrbitObject
    object_b: OrbitObject
    tca: datetime
    miss_distance_m: float
    relative_speed_mps: float
    window_start: datetime
    window_end: datetime
    screening_risk: str
    data_retrieved_at: datetime


def risk_from_distance_km(miss_km: float, settings: Settings) -> str:
    if miss_km <= settings.high_risk_distance_km:
        return "HIGH"
    if miss_km <= settings.medium_risk_distance_km:
        return "MEDIUM"
    return "LOW"


def _pair_refine(a: OrbitObject, b: OrbitObject, coarse_t: datetime, window_start: datetime, window_end: datetime, coarse_step_seconds: int, refine_step_seconds: int, settings: Settings) -> Conjunction | None:
    refine_start = max(window_start, coarse_t - timedelta(seconds=coarse_step_seconds))
    refine_end = min(window_end, coarse_t + timedelta(seconds=coarse_step_seconds))
    times = make_time_grid(refine_start, refine_end, refine_step_seconds)
    if len(times) < 2:
        return None

    pa = propagate_satellite(a.sat, times)
    pb = propagate_satellite(b.sat, times)
    valid = (pa.errors == 0) & (pb.errors == 0)
    if not np.any(valid):
        return None

    delta = pa.teme_pos_km - pb.teme_pos_km
    d_km = np.linalg.norm(delta, axis=1)
    d_km[~valid] = np.inf
    idx = int(np.argmin(d_km))
    if not np.isfinite(d_km[idx]):
        return None

    rel_speed_mps = float(np.linalg.norm(pa.teme_vel_km_s[idx] - pb.teme_vel_km_s[idx]) * 1000.0)
    miss_m = float(d_km[idx] * 1000.0)
    return Conjunction(
        object_a=a,
        object_b=b,
        tca=times[idx],
        miss_distance_m=miss_m,
        relative_speed_mps=rel_speed_mps,
        window_start=window_start,
        window_end=window_end,
        screening_risk=risk_from_distance_km(miss_m / 1000.0, settings),
        data_retrieved_at=min(a.retrieved_at, b.retrieved_at),
    )


def screen_conjunctions(objects: list[OrbitObject], window_hours: float, coarse_step_seconds: int, refine_step_seconds: int, broadphase_distance_km: float, settings: Settings) -> list[Conjunction]:
    if len(objects) < 2:
        return []

    now = datetime.now(timezone.utc)
    window_end = now + timedelta(hours=window_hours)
    times = make_time_grid(now, window_end, coarse_step_seconds)

    # Pre-propagate all objects once on the coarse grid.
    coarse_states = []
    for obj in objects:
        result = propagate_satellite(obj.sat, times)
        coarse_states.append(result)

    candidate_pairs: set[tuple[int, int]] = set()
    broadphase_m = broadphase_distance_km * 1000.0

    for ti in range(len(times)):
        points = np.array([coarse_states[i].ecef_km[ti] for i in range(len(objects))]) * 1000.0
        finite = np.all(np.isfinite(points), axis=1)
        valid_idx = np.where(finite)[0]
        if len(valid_idx) < 2:
            continue
        tree = cKDTree(points[finite])
        for local_i, local_j in tree.query_pairs(r=broadphase_m):
            i = int(valid_idx[local_i])
            j = int(valid_idx[local_j])
            candidate_pairs.add((min(i, j), max(i, j)))

    conjunctions: list[Conjunction] = []
    for i, j in sorted(candidate_pairs):
        d = np.linalg.norm(coarse_states[i].teme_pos_km - coarse_states[j].teme_pos_km, axis=1)
        valid = (coarse_states[i].errors == 0) & (coarse_states[j].errors == 0)
        d[~valid] = np.inf
        if not np.isfinite(d).any():
            continue
        coarse_idx = int(np.argmin(d))
        event = _pair_refine(objects[i], objects[j], times[coarse_idx], now, window_end, coarse_step_seconds, refine_step_seconds, settings)
        if event:
            conjunctions.append(event)

    conjunctions.sort(key=lambda e: e.miss_distance_m)
    return conjunctions
