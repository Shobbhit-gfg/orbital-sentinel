"""Deterministic TEME -> Earth-fixed conversion and WGS84 geodetic helpers.

This is intentionally self-contained for the MVP. The Earth-fixed conversion uses
Greenwich mean sidereal time; polar motion and UT1-UTC EOP corrections are not
included. Operational SSA should use a full EOP-aware transformation.
"""
from datetime import datetime, timezone
import math
import numpy as np

WGS84_A_M = 6378137.0
WGS84_F = 1.0 / 298.257223563
WGS84_E2 = WGS84_F * (2.0 - WGS84_F)


def datetime_to_jd(dt: datetime) -> tuple[float, float]:
    dt = dt.astimezone(timezone.utc)
    year = dt.year
    month = dt.month
    day_fraction = (
        dt.day
        + (dt.hour + dt.minute / 60.0 + dt.second / 3600.0 + dt.microsecond / 3.6e9) / 24.0
    )
    if month <= 2:
        year -= 1
        month += 12
    a = year // 100
    b = 2 - a + a // 4
    jd = math.floor(365.25 * (year + 4716)) + math.floor(30.6001 * (month + 1)) + day_fraction + b - 1524.5
    return float(jd), 0.0


def _gmst_rad(jd: np.ndarray) -> np.ndarray:
    """Greenwich mean sidereal angle, radians, for UTC Julian date.

    Uses a deterministic approximation sufficient for this visualization/screening MVP.
    """
    t = (jd - 2451545.0) / 36525.0
    seconds = (
        67310.54841
        + (876600.0 * 3600.0 + 8640184.812866) * t
        + 0.093104 * t * t
        - 6.2e-6 * t * t * t
    )
    seconds = np.mod(seconds, 86400.0)
    return seconds * (2.0 * np.pi / 86400.0)


def teme_to_ecef_km(r_teme_km: np.ndarray, jd: np.ndarray) -> np.ndarray:
    """Rotate same-epoch TEME positions into an Earth-fixed frame.

    Inputs:
        r_teme_km: shape (..., 3)
        jd: shape (...,)
    Returns:
        shape (..., 3), km
    """
    theta = _gmst_rad(np.asarray(jd, dtype=float))
    c = np.cos(theta)
    s = np.sin(theta)
    x = r_teme_km[..., 0]
    y = r_teme_km[..., 1]
    z = r_teme_km[..., 2]
    return np.stack((c * x + s * y, -s * x + c * y, z), axis=-1)


def ecef_to_geodetic(r_ecef_km: np.ndarray) -> np.ndarray:
    """ECEF km -> geodetic [lat_deg, lon_deg, height_km] on WGS84."""
    xyz_m = np.asarray(r_ecef_km, dtype=float) * 1000.0
    x, y, z = xyz_m[..., 0], xyz_m[..., 1], xyz_m[..., 2]
    lon = np.arctan2(y, x)
    p = np.hypot(x, y)
    lat = np.arctan2(z, p * (1.0 - WGS84_E2))

    for _ in range(7):
        sin_lat = np.sin(lat)
        n = WGS84_A_M / np.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
        h = p / np.cos(lat) - n
        lat = np.arctan2(z, p * (1.0 - WGS84_E2 * n / (n + h)))

    sin_lat = np.sin(lat)
    n = WGS84_A_M / np.sqrt(1.0 - WGS84_E2 * sin_lat * sin_lat)
    h = p / np.cos(lat) - n
    return np.stack((np.degrees(lat), np.degrees(lon), h / 1000.0), axis=-1)
