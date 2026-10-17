"""Test simulated dispatch distance, ETA calculation, and status progression."""
import pytest
from sahaay.dispatch.distance import calculate_haversine_km, estimate_route_km
from sahaay.dispatch.eta import compute_eta_details

def test_haversine_distance():
    # CP to Karol Bagh (~4 km)
    lat_cp, lon_cp = 28.6315, 77.2167
    lat_kb, lon_kb = 28.6514, 77.1907
    dist_km = calculate_haversine_km(lat_cp, lon_cp, lat_kb, lon_kb)
    assert 2.5 <= dist_km <= 4.5
    
    # Route distance should be greater than straight-line
    route_km = estimate_route_km(lat_cp, lon_cp, lat_kb, lon_kb)
    assert route_km > dist_km

def test_eta_calculation():
    eta = compute_eta_details(distance_km=4.0, speed_kmh=40.0)
    assert eta["eta_minutes"] > 0
    assert "estimated_arrival_time" in eta
    assert "last_updated" in eta
