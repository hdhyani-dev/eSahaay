"""Geographic extraction, Delhi NCR gazetteer and spatial relationship parsing.
Reference: FR-2.1
"""
import re
import math
from typing import List, Dict, Optional, Tuple, Any
from rapidfuzz import fuzz

# Curated Delhi NCR Gazetteer with representative GPS coordinates
DELHI_GAZETTEER = {
    # Localities & Sectors
    "rajendra nagar": {"lat": 28.6389, "lon": 77.1788, "type": "locality", "pincode": "110060"},
    "karol bagh": {"lat": 28.6514, "lon": 77.1907, "type": "locality", "pincode": "110005"},
    "rohini": {"lat": 28.7495, "lon": 77.0565, "type": "locality", "pincode": "110085"},
    "sector 14 rohini": {"lat": 28.7180, "lon": 77.1325, "type": "locality", "pincode": "110085"},
    "sector 15 rohini": {"lat": 28.7215, "lon": 77.1310, "type": "locality", "pincode": "110085"},
    "shalimar bagh": {"lat": 28.7164, "lon": 77.1584, "type": "locality", "pincode": "110088"},
    "patel nagar": {"lat": 28.6538, "lon": 77.1644, "type": "locality", "pincode": "110008"},
    "connaught place": {"lat": 28.6315, "lon": 77.2167, "type": "locality", "pincode": "110001"},
    "cp": {"lat": 28.6315, "lon": 77.2167, "type": "locality", "pincode": "110001"},
    "dwarka": {"lat": 28.5921, "lon": 77.0460, "type": "locality", "pincode": "110075"},
    "janakpuri": {"lat": 28.6219, "lon": 77.0878, "type": "locality", "pincode": "110058"},
    "saket": {"lat": 28.5244, "lon": 77.2167, "type": "locality", "pincode": "110017"},
    "lajpat nagar": {"lat": 28.5677, "lon": 77.2433, "type": "locality", "pincode": "110024"},
    "hauz khas": {"lat": 28.5494, "lon": 77.2001, "type": "locality", "pincode": "110016"},
    "chandni chowk": {"lat": 28.6506, "lon": 77.2303, "type": "locality", "pincode": "110006"},
    "pitampura": {"lat": 28.6990, "lon": 77.1384, "type": "locality", "pincode": "110034"},
    "preet vihar": {"lat": 28.6385, "lon": 77.2965, "type": "locality", "pincode": "110092"},
    "mayur vihar": {"lat": 28.6075, "lon": 77.2995, "type": "locality", "pincode": "110091"},
    "uttam nagar": {"lat": 28.6212, "lon": 77.0583, "type": "locality", "pincode": "110059"},
    "noida sector 18": {"lat": 28.5708, "lon": 77.3271, "type": "locality", "pincode": "201301"},
    "gurugram cyber hub": {"lat": 28.4950, "lon": 77.0895, "type": "locality", "pincode": "122002"},
    "okhla phase 2": {"lat": 28.5284, "lon": 77.2731, "type": "locality", "pincode": "110020"},
    "okhla": {"lat": 28.5300, "lon": 77.2700, "type": "locality", "pincode": "110020"},
    "dhaula kuan": {"lat": 28.5921, "lon": 77.1610, "type": "locality", "pincode": "110010"},
    "cr park": {"lat": 28.5385, "lon": 77.2490, "type": "locality", "pincode": "110019"},
    "chittaranjan park": {"lat": 28.5385, "lon": 77.2490, "type": "locality", "pincode": "110019"},
    "t nagar": {"lat": 28.6514, "lon": 77.1907, "type": "locality", "pincode": "110005"},
    "indiranagar": {"lat": 28.6389, "lon": 77.1788, "type": "locality", "pincode": "110060"},
    "almora": {"lat": 28.7180, "lon": 77.1325, "type": "locality", "pincode": "110085"},

    # Landmarks & Metro Stations
    "rajiv chowk metro": {"lat": 28.6328, "lon": 77.2195, "type": "metro_station"},
    "kashmere gate": {"lat": 28.6675, "lon": 77.2285, "type": "metro_station"},
    "aiims": {"lat": 28.5672, "lon": 77.2100, "type": "hospital"},
    "safdarjung hospital": {"lat": 28.5686, "lon": 77.2072, "type": "hospital"},
    "ram manohar lohia": {"lat": 28.6247, "lon": 77.2023, "type": "hospital"},
    "india gate": {"lat": 28.6129, "lon": 77.2295, "type": "landmark"}
}

# Spatial preposition patterns in Hinglish
SPATIAL_PATTERNS = [
    r'(?:ke\s+paas|k\s+pas|near|opposite|ke\s+samne|ke\s+saamne|bagal\s+mein|ke\s+peeche|piche)\s+([A-Za-z0-9\s]+?)(?=[,\.]|$|aur|and|help|jaldi)',
    r'(?:gali\s+no|gali\s+number|lane\s+no)\s*[:#]?\s*(\d+[A-Za-z]?)',
    r'(?:makan\s+no|house\s+no|flat\s+no)\s*[:#]?\s*(\d+[A-Za-z]?)',
    r'(?:sector|sec)\s*[:#]?\s*(\d+)',
    r'(?:block|blk)\s*[:#]?\s*([A-Za-z0-9]+)',
    r'\b(110\d{3}|201\d{3}|122\d{3})\b' # Delhi NCR pincodes
]

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate straight-line distance in kilometers between two GPS coordinates."""
    R = 6371.0 # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return round(R * c, 2)

def extract_location_candidates(text: str) -> List[Dict[str, Any]]:
    """
    Extract place names, landmarks, relative directions, and pincodes from transcript.
    Returns ranked candidates with coordinates and confidence.
    """
    candidates = []
    text_lower = text.lower()
    
    # 1. Exact & Fuzzy matching against Delhi Gazetteer
    for place, meta in DELHI_GAZETTEER.items():
        if place in text_lower:
            candidates.append({
                "text": place.title(),
                "type": meta["type"],
                "confidence": 0.95,
                "lat": meta["lat"],
                "lon": meta["lon"],
                "source": "gazetteer_exact"
            })
        elif len(place) > 6 and fuzz.partial_ratio(place, text_lower) >= 90:
            candidates.append({
                "text": place.title(),
                "type": meta["type"],
                "confidence": 0.82,
                "lat": meta["lat"],
                "lon": meta["lon"],
                "source": "gazetteer_fuzzy"
            })
            
    # 2. Extract Relative Spatial phrases (e.g. "school ke peeche", "metro gate no 2")
    rel_match = re.search(r'([A-Za-z0-9\s]{3,20}\s+(?:ke\s+paas|ke\s+peeche|ke\s+samne|bagal\s+mein))', text_lower)
    if rel_match:
        span = rel_match.group(1).strip()
        candidates.append({
            "text": span.title(),
            "type": "relative_direction",
            "confidence": 0.75,
            "lat": 28.6139, # Default city centroid for relative until resolved
            "lon": 77.2090,
            "source": "spatial_syntax"
        })
        
    # 3. Extract Gali / House / Sector specific details
    gali_match = re.search(r'(gali\s+no(?:umber)?\s*\d+|sector\s*\d+|block\s*[a-z0-9]+)', text_lower)
    if gali_match:
        span = gali_match.group(1).strip()
        candidates.append({
            "text": span.title(),
            "type": "sub_locality",
            "confidence": 0.85,
            "lat": candidates[0]["lat"] if candidates else 28.6139,
            "lon": candidates[0]["lon"] if candidates else 77.2090,
            "source": "address_syntax"
        })

    # Deduplicate candidates by text
    seen = set()
    deduped = []
    for c in sorted(candidates, key=lambda x: -x["confidence"]):
        if c["text"].lower() not in seen:
            seen.add(c["text"].lower())
            deduped.append(c)
            
    return deduped
