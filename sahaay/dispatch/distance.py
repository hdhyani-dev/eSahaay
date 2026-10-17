"""Distance calculations using Haversine formula and route factor approximations.
Reference: Section 9 - Distance and ETA
"""
import math
from typing import Tuple

def calculate_haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate straight-line distance in kilometers using Haversine formula.
    Clearly labeled as approximate straight-line distance.
    """
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2)**2 + 
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def estimate_route_km(lat1: float, lon1: float, lat2: float, lon2: float, urban_factor: float = 1.30) -> float:
    """
    Simulated road network driving distance using urban circuity factor.
    Labled as estimated road distance.
    """
    straight_line = calculate_haversine_km(lat1, lon1, lat2, lon2)
    return round(straight_line * urban_factor, 2)
