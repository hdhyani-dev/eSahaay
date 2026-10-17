"""Synthetic dataset generation and curated evaluation splits.
Reference: Section 8.4, Section 10.1
"""
from typing import List, Dict, Any

# Curated synthetic dataset representing realistic helpline diversity
VALIDATION_DATASET: List[Dict[str, Any]] = [
    {
        "id": "VAL-001",
        "raw_text": "bhaiya jaldi aao, ghar me pati maar raha hai, Sector 14 Rohini, bacche ro rahe",
        "true_urgency": "P0",
        "true_threat": "domestic_violence",
        "true_routes": ["police", "shelter"],
        "true_location": "Sector 14 Rohini",
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-002",
        "raw_text": "hello... wrong number... aap pizza wali ho? ... nahi wo mera bhai yahin hai (whisper, then silence)",
        "true_urgency": "P1",
        "true_threat": "domestic_violence",
        "true_routes": ["police", "shelter"],
        "true_location": None,
        "is_covert": True,
        "language": "Hinglish",
        "noise_level": "medium"
    },
    {
        "id": "VAL-003",
        "raw_text": "meri maa ko saans nahi aa rahi, Karol Bagh gali no 4, jaldi ambulance bhejo",
        "true_urgency": "P0",
        "true_threat": "medical_emergency",
        "true_routes": ["medical"],
        "true_location": "Karol Bagh",
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-004",
        "raw_text": "wahi aadmi phir peecha kar raha hai, pichle hafte bhi call kiya tha, metro station ke paas",
        "true_urgency": "P1",
        "true_threat": "stalking_harassment",
        "true_routes": ["police", "legal"],
        "true_location": "Metro Station",
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-005",
        "raw_text": "talaq ke baad mehr ka paisa kaise milega, kanooni salaah chahiye",
        "true_urgency": "P3",
        "true_threat": "legal_query",
        "true_routes": ["legal"],
        "true_location": None,
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-006",
        "raw_text": "ek large cheese pizza bhej do jaldi se jaldi... haan delivery address Rajendra Nagar hai",
        "true_urgency": "P1",
        "true_threat": "domestic_violence",
        "true_routes": ["police", "shelter"],
        "true_location": "Rajendra Nagar",
        "is_covert": True,
        "language": "Hinglish",
        "noise_level": "medium"
    },
    {
        "id": "VAL-007",
        "raw_text": "chaku dikha ke paise maang rahe hain Connaught Place outer circle par, bachao",
        "true_urgency": "P0",
        "true_threat": "domestic_violence",
        "true_routes": ["police"],
        "true_location": "Connaught Place",
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-008",
        "raw_text": "papa behosh ho gaye hain achanak se, chhati me bohot tez dard tha, Shalimar Bagh",
        "true_urgency": "P0",
        "true_threat": "medical_emergency",
        "true_routes": ["medical"],
        "true_location": "Shalimar Bagh",
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-009",
        "raw_text": "sasural wale dahej ke liye taane marte hain, kal ladai hui thi, abhi main theek hoon lekin complaint karni hai",
        "true_urgency": "P2",
        "true_threat": "domestic_violence",
        "true_routes": ["police", "shelter", "legal"],
        "true_location": None,
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-010",
        "raw_text": "doctor sahab se baat karwa do... dawai nahi mil rahi... kamre se nikalne nahi de rahe",
        "true_urgency": "P1",
        "true_threat": "trafficking_coercion",
        "true_routes": ["police", "shelter"],
        "true_location": None,
        "is_covert": True,
        "language": "Hinglish",
        "noise_level": "medium"
    },
    {
        "id": "VAL-011",
        "raw_text": "mujhe DLSA helpline ka number chahiye court case ke liye",
        "true_urgency": "P3",
        "true_threat": "legal_query",
        "true_routes": ["legal"],
        "true_location": None,
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-012",
        "raw_text": "bhaiya wo ladka roz bus stop Janakpuri par badtameezi karta hai",
        "true_urgency": "P2",
        "true_threat": "stalking_harassment",
        "true_routes": ["police", "legal"],
        "true_location": "Janakpuri",
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "low"
    },
    {
        "id": "VAL-013",
        "raw_text": "khun nikal rha bohot sar se accident hua hai Patel Nagar chowk jaldi aao",
        "true_urgency": "P0",
        "true_threat": "medical_emergency",
        "true_routes": ["medical", "police"],
        "true_location": "Patel Nagar",
        "is_covert": False,
        "language": "Hinglish (Noisy ASR)",
        "noise_level": "high"
    },
    {
        "id": "VAL-014",
        "raw_text": "sorry galat number lag gaya lagta hai... haan doodh ka packet le aana (fusfusahat)",
        "true_urgency": "P1",
        "true_threat": "domestic_violence",
        "true_routes": ["police", "shelter"],
        "true_location": None,
        "is_covert": True,
        "language": "Hinglish",
        "noise_level": "medium"
    },
    {
        "id": "VAL-015",
        "raw_text": "baccha akele ro raha hai sadak par Pitampura metro ke paas koi nahi hai sath",
        "true_urgency": "P1",
        "true_threat": "child_at_risk",
        "true_routes": ["police", "shelter"],
        "true_location": "Pitampura",
        "is_covert": False,
        "language": "Hinglish",
        "noise_level": "medium"
    }
]

# Hidden-style test set with withheld labels for hidden evaluation protocol
HIDDEN_STYLE_DATASET: List[Dict[str, Any]] = [
    {
        "id": "HID-101",
        "raw_text": "bhaiya goli chal rahi hai samne, Saket market me jaldi police bhejo",
        "true_urgency": "P0",
        "true_threat": "domestic_violence",
        "true_routes": ["police"],
        "true_location": "Saket"
    },
    {
        "id": "HID-102",
        "raw_text": "ek extra cheese pizza send kar do... gali no 12 Lajpat Nagar (dheere se bola)",
        "true_urgency": "P1",
        "true_threat": "domestic_violence",
        "true_routes": ["police", "shelter"],
        "true_location": "Lajpat Nagar"
    },
    {
        "id": "HID-103",
        "raw_text": "mera bhai chhat se gir gaya hai behosh pada hai Hauz Khas village me",
        "true_urgency": "P0",
        "true_threat": "medical_emergency",
        "true_routes": ["medical"],
        "true_location": "Hauz Khas"
    },
    {
        "id": "HID-104",
        "raw_text": "padosi roz kooda fekta hai hamare darwaze par, samjhate hain toh ladta hai",
        "true_urgency": "P2",
        "true_threat": "other",
        "true_routes": ["police"],
        "true_location": None
    },
    {
        "id": "HID-105",
        "raw_text": "bacchon ki custody lene ke liye court me kya karna hoga vakeel ka kharcha",
        "true_urgency": "P3",
        "true_threat": "legal_query",
        "true_routes": ["legal"],
        "true_location": None
    }
]
