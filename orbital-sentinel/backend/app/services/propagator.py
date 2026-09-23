from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone, timedelta
import numpy as np

from sgp4.api import Satrec

from .frames import datetime_to_jd, teme_to_ecef_km, ecef_to_geodetic


@dataclass
class PropagationResult:
    times: list[datetime]
    teme_pos_km: np.ndarray
    teme_vel_km_s: np.ndarray
    ecef_km: np.ndarray
    geodetic: np.ndarray
    errors: np.ndarray


def datetimes_to_jd(times: list[datetime]) -> tuple[np.ndarray, np.ndarray]:
    pairs = [datetime_to_jd(t) for t in times]
    return np.array([p[0] for p in pairs], dtype=float), np.array([p[1] for p in pairs], dtype=float)


def propagate_satellite(sat: Satrec, times: list[datetime]) -> PropagationResult:
    jd, fr = datetimes_to_jd(times)
    errors, positions, velocities = sat.sgp4_array(jd, fr)
    positions = np.asarray(positions, dtype=float)
    velocities = np.asarray(velocities, dtype=float)
    ecef = teme_to_ecef_km(positions, jd + fr)
    geodetic = ecef_to_geodetic(ecef)
    return PropagationResult(
        times=[t.astimezone(timezone.utc) for t in times],
        teme_pos_km=positions,
        teme_vel_km_s=velocities,
        ecef_km=ecef,
        geodetic=geodetic,
        errors=np.asarray(errors),
    )


def make_time_grid(start: datetime, end: datetime, step_seconds: int) -> list[datetime]:
    start = start.astimezone(timezone.utc)
    end = end.astimezone(timezone.utc)
    if end < start:
        raise ValueError("end must be after start")
    step = timedelta(seconds=step_seconds)
    times: list[datetime] = []
    cursor = start
    while cursor <= end:
        times.append(cursor)
        cursor += step
    if times[-1] < end:
        times.append(end)
    return times
