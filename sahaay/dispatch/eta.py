"""Estimated Time of Arrival (ETA) calculation engine.
Reference: Section 9 - ETA calculations
"""
import datetime
from typing import Dict, Any

def compute_eta_details(
    distance_km: float,
    speed_kmh: float = 40.0,
    prep_overhead_minutes: float = 1.5,
    traffic_multiplier: float = 1.15
) -> Dict[str, Any]:
    """
    Calculate simulated ETA and timestamps based on distance, vehicle speed and urban traffic.
    Never claims to be live GPS traffic. Labeled as simulated estimation.
    """
    if speed_kmh <= 0:
        speed_kmh = 40.0
        
    travel_time_hours = (distance_km * traffic_multiplier) / speed_kmh
    travel_minutes = round((travel_time_hours * 60) + prep_overhead_minutes, 1)
    
    # Cap minimum response time to 2 minutes
    travel_minutes = max(2.0, travel_minutes)
    
    now = datetime.datetime.utcnow()
    estimated_arrival_dt = now + datetime.timedelta(minutes=travel_minutes)
    
    return {
        "eta_minutes": travel_minutes,
        "distance_remaining_km": round(distance_km, 2),
        "estimated_arrival_time": estimated_arrival_dt.strftime("%H:%M:%S UTC"),
        "last_updated": now.strftime("%H:%M:%S UTC"),
        "traffic_factor": "Medium Urban (Simulated 1.15x)"
    }
