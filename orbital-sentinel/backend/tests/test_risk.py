from app.services.screening import risk_from_distance_km


class S:
    high_risk_distance_km = 1.0
    medium_risk_distance_km = 5.0


def test_risk_thresholds():
    assert risk_from_distance_km(0.5, S) == "HIGH"
    assert risk_from_distance_km(2.0, S) == "MEDIUM"
    assert risk_from_distance_km(20.0, S) == "LOW"
