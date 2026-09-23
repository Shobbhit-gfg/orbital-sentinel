from datetime import datetime, timezone
import numpy as np
from app.services.frames import ecef_to_geodetic, teme_to_ecef_km


def test_rotation_preserves_radius():
    r = np.array([[7000.0, 0.0, 0.0]])
    jd = np.array([2460000.5])
    out = teme_to_ecef_km(r, jd)
    assert np.allclose(np.linalg.norm(r, axis=1), np.linalg.norm(out, axis=1), rtol=1e-12)


def test_geodetic_equator():
    r = np.array([[6378.137, 0.0, 0.0]])
    geo = ecef_to_geodetic(r)
    assert abs(geo[0, 0]) < 1e-8
    assert abs(geo[0, 1]) < 1e-8
    assert abs(geo[0, 2]) < 1e-3
