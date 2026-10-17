"""M2 Extractor: Structured fact extraction from Hinglish helpline transcripts.
Reference: FR-2.2, FR-2.3, FR-2.4
"""
import re
from typing import Dict, List, Any, Optional, Tuple
from rapidfuzz import fuzz
from sahaay.triage.geo import extract_location_candidates

# Threat taxonomy patterns in Pan-Indian languages (Hinglish, Tamil, Bengali, Kannada, Kumaoni, etc.)
THREAT_KEYWORDS = {
    "domestic_violence": [
        "pati maar", "pati ne maara", "marpeet", "sasural", "dahej", "gharelu hinsa",
        "husband beating", "room mein band", "ghar me maar", "kamre me band", "pitai",
        "मार रहा", "पीटा", "घरेलू हिंसा", "दहेज",
        # Tamil / Tanglish
        "kaapaathunga", "kanavan adikkiraanga", "purushan adikkiraanga", "adikkiran", "veetula pooti", "udhavi thevai", "காப்பாத்துங்க", "கணவன் அடிக்கிறார்",
        # Bengali / Banglish
        "bachan", "shami marchhe", "marche", "sahajjo korun", "shami aamake", "বাঁচান", "স্বামী মারছে", "মারধর",
        # Kannada / Kanglish
        "sahaya madi", "ganda hodeyuthiddane", "hodeyutiddane", "bachasi", "hodiya", "mane olage bandhana", "ಸಹಾಯ ಮಾಡಿ", "ಗಂಡ ಹೊಡೆಯುತ್ತಿದ್ದಾನೆ",
        # Kumaoni / Pahari / Garhwali
        "madat kara", "khasam maran laagi", "marpeet karni cha", "ghar ma band cha", "khasam", "मदद करा", "मार पीट", "खसम",
        # Telugu / Marathi / Gujarati
        "kapadandi", "bhartha koduthunnadu", "sahayam", "navra martoy", "marhan", "pati mare chhe", "marpit", "కాపాడండి", "मदत करा"
    ],
    "sexual_violence": [
        "chedkhani", "chhedkhani", "zabardasti", "molestation", "rape", "touch kar",
        "kapde faad", "galat harkat", "badtameezi", "छेड़खानी", "जबरदस्ती", "बलात्कार",
        "pallu iluthu", "thappana nadathai", "kharap byabohar", "chedchad"
    ],
    "medical_emergency": [
        "saans nahi", "sans nahi", "chest pain", "sine me dard", "seene mein dard", "dil ka daura",
        "behosh", "unconscious", "heart attack", "chakar aa", "blood nikal", "khoon beh", "serious accident",
        "ambulance", "एम्बुलेंस", "साँस", "सांस", "सीने में दर्द", "बेहोश", "हार्ट अटैक",
        # Tamil
        "nenju vali", "moochu thinaral", "maruthuva udhavi", "ambulance thevai", "mayakkam", "ratham", "கை கால்", "நெஞ்சு வலி", "மூச்சு",
        "kai kaal asaiyaama", "stroke pola", "paralysis stroke", "vaai saanjiduchi", "icu ambulance", "stroke",
        # Bengali
        "buker betha", "shash kosto", "rokto porche", "osustho", "ambulance dorkar", "বুকের ব্যথা", "শ্বাসকষ্ট", "রক্ত",
        # Kannada
        "ede novu", "usirata tondare", "raktha harithide", "bekagide ambulance", "aspatre", "taleyinda thumbe raktha", "ಎದೆ ನೋವು", "ಉಸಿರಾಟ",
        # Kumaoni / Pahari
        "chhati ma peed", "saas ni auni", "khoon bagan laago", "gaddi ulati", "chot lagi cha", "छाती में पीड़ा", "सांस नी आउनी",
        # Telugu / Marathi / Gujarati
        "gunde noppi", "oopiri aadatledu", "raktham", "chhati dukhate", "rakta yetoy", "chhati ma dukhaye", "lohi", "గుండె నొప్పి"
    ],
    "accident_fire": [
        "aag lag gayi", "fire", "cylinder blast", "gadi thuk gayi", "car accident", "bike slip", "road accident",
        "आग लग", "एक्सीडेंट", "दुर्घटना",
        # Tamil
        "thee pidithadhu", "thee", "vibathu", "car vibathu", "cylinder vedithadhu", "தீ", "விபத்து",
        # Bengali
        "agun legeche", "durghatona", "cylinder bisfuron", "gari accident", "meter box theke", "bishal agun", "kaalo dhnowa", "aatke aache", "আগুন লেগেছে", "দুর্ঘটনা",
        # Kannada
        "benki bithu", "aparadha", "benki tagulide", "gaadi accident", "cylinder spotavagide", "speeding lorry", "bike ge guddhittu", "rider biddu", "ಬೆಂಕಿ", "ಅಪಘಾತ",
        # Kumaoni / Pahari
        "aag lagige", "pahad se gadi giri", "sadak hadsa", "pahad bata gaddi palti", "dhoong pado", "khayi ma ulti", "yatri fasa", "gas cutter", "आग लगीगे", "सड़क हादसा",
        # Telugu / Marathi / Gujarati
        "manta tagilindi", "pramadam", "cylinder pelindi", "aag lagli", "apghat", "aag lagi chhe", "akshmat"
    ],
    "stalking_harassment": [
        "peecha kar raha", "picha kar raha", "following me", "wahi aadmi", "wahi ladka",
        "phone pe dhamki", "call karke pareshan", "stalking", "harass", "पीछा कर रहा", "धमकी",
        # Tamil, Bengali, Kannada, Telugu, Kumaoni
        "pinnadi varan", "pin thodargiran", "thollai panran", "பின்தொடர்கிறான்",
        "pichone asche", "pechone lagche", "domki dichhe", "পিছু নিচ্ছে",
        "hinde barthiddane", "hedrike aagthide", "stalk madthiddane", "ಹಿಂದೆ ಬರುತ್ತಿದ್ದಾನೆ",
        "picha karan ro", "dhamki di ro", "ventapaduthunnadu", "bhayamesthondi"
    ],
    "child_at_risk": [
        "bacche ro rahe", "bacha ro rahe", "bacche ko maar", "chhota bacha", "minor girl", "child labour", "baccha akela",
        "बच्चे रो रहे", "बच्चा रो रहा", "kuzhandhai", "chhotoder", "makkalu"
    ],
    "trafficking_coercion": [
        "jabardasti laya", "bandhak banaya", "passport cheen liya", "paisa maang rahe", "room me lock", "doctor dawai",
        "बंधक", "तस्करी"
    ],
    "mental_health_crisis": [
        "khudkushi", "suicide", "jaan de dunga", "marne ka man", "depression", "panicking", "bura lag raha",
        "खुदकुशी", "आत्महत्या", "tharkolai", "aatmahatya"
    ],
    "legal_query": [
        "talaq", "divorce", "mehr", "court", "vakil", "kanooni", "legal aid", "maintenance", "dhara",
        "तलाक", "कानूनी", "कोर्ट", "वकील", "sattam"
    ]
}

# Detail keywords
VICTIM_PATTERNS = {
    "self": ["main", "mujhe", "mera", "meri", "i am", "me", "நான்", "enakku", "aami", "aamake", "naanu", "nanage", "मैं", "मुझे"],
    "mother": ["maa", "mummy", "mataji", "ammi", "amma", "thaai", "mayer", "avva", "माँ", "माताजी"],
    "father": ["papa", "pitaji", "abbu", "father", "appa", "baba", "thande", "पापा", "पिताजी"],
    "child": ["baccha", "bacche", "bache", "beti", "beta", "chhota", "kids", "kuzhandhai", "chele", "meye", "makkalu", "बच्चे", "बच्चा"],
    "sister": ["behen", "didi", "chhoti behen", "thangai", "akka", "bon", "thangi", "बहन", "दीदी"],
    "friend": ["dost", "friend", "saheli", "nanban", "dostho", "snehide", "दोस्त", "सहेली"]
}

PERPETRATOR_PATTERNS = {
    "husband": ["pati", "husband", "shohar", "kanavan", "purushan", "shami", "bor", "ganda", "khasam", "bhyola", "bhartha", "navra", "पति", "शौहर", "கணவன்", "স্বামী", "ಗಂಡ", "खसम", "భర్త"],
    "in_laws": ["saas", "sasur", "devar", "jeth", "sasural", "maamiyaar", "shashuri", "athhe", "maava", "सास", "ससुर"],
    "stranger": ["wahi aadmi", "wahi ladka", "anjan", "bike wala", "unknown guy", "theriyadhavar", "acchena lok", "gothilladavaru", "अजनबी"],
    "neighbour": ["padosi", "neighbour", "samne wala", "pakkathu veedu", "protibeshi", "pakka mane", "पड़ोसी"],
    "partner": ["boyfriend", "live in partner", "friend"]
}

WEAPON_PATTERNS = {
    "knife": ["chaku", "chaaku", "chhuri", "blade", "knife", "katthi", "katti", "चाकू", "छुरी", "கத்தி", "ছুরি", "ಕತ್ತಿ"],
    "firearm": ["bandook", "gun", "pistol", "tamancha", "katta", "thuppakki", "बंदूक", "पिस्तौल"],
    "blunt_object": ["danda", "lathi", "rod", "iron rod", "bottle", "eent", "brick", "kambi", "lathi", "kole", "डंडा", "लाठी"]
}

INJURY_PATTERNS = {
    "bleeding": ["khoon", "khun", "blood", "bleeding", "zakhm", "ratham", "rokto", "raktha", "raktham", "lohi", "खून", "रक्त", "ரத்தம்", "রক্ত"],
    "breathing_difficulty": ["saans nahi", "sans nahi", "breathless", "asthma", "moochu thinaral", "shash kosto", "usirata tondare", "saas ni auni", "साँस", "सांस", "மூச்சு"],
    "chest_pain": ["chest pain", "sine me dard", "seene mein dard", "chhati dard", "nenju vali", "buker betha", "ede novu", "gunde noppi", "chhati ma peed", "सीने में दर्द", "दर्द", "நெஞ்சு வலி"],
    "unconscious": ["behosh", "unconscious", "hosh nahi", "faint", "mayakkam", "ggyan harano", "spruha ledu", "बेहोश"],
    "fracture_trauma": ["haddi toot", "fracture", "chot", "head injury", "elumbu murivu", "haad bhanga", "moolo murithu", "चोट"]
}

def extract_threat_types(text: str, raw_text: Optional[str] = None) -> List[Dict[str, Any]]:
    """Classify threat types with probabilities from keywords and context."""
    text_lower = (text + " " + (raw_text or "")).lower().strip()
    if not text_lower:
        return [{
            "type": "other",
            "p": 0.50,
            "description": "General Helpline Query"
        }]

    predictions = []
    
    # Contextual multi-word checks across Pan-Indian languages
    has_pati = any(k in text_lower for k in [
        "pati", "husband", "shohar", "kanavan", "purushan", "shami", "ganda", "khasam", "bhyola", "bhartha", "navra",
        "पति", "शौहर", "கணவன்", "স্বামী", "ಗಂಡ", "खसम", "భర్త"
    ])
    has_violence = any(k in text_lower for k in [
        "maar", "mar", "chaku", "pitai", "beating", "adikkira", "marchhe", "hodey", "marpeet", "maran", "koduthu", "martoy",
        "chhuri", "katthi", "katti", "पीटा", "मार", "அடி", "মার", "ಹೊಡೆ", "కొట్టు"
    ])
    if has_pati and has_violence:
        predictions.append({
            "type": "domestic_violence",
            "p": 0.95,
            "description": "Domestic Violence"
        })

    has_child = any(k in text_lower for k in ["bacche", "bacha", "bache", "kids", "kuzhandhai", "chhotoder", "makkalu", "pillalu", "बच्चे"])
    has_crying_danger = any(k in text_lower for k in ["ro rahe", "maar", "danger", "azhuguraanga", "kandche", "aluthiddare", "रो रहे"])
    if has_child and has_crying_danger:
        predictions.append({
            "type": "child_at_risk",
            "p": 0.90,
            "description": "Child At Risk"
        })

    has_cardiac_breath = any(k in text_lower for k in [
        "saans", "sans", "chest", "sine", "seene", "behosh", "ambulance",
        "nenju vali", "moochu", "buker betha", "shash kosto", "ede novu", "usirata", "gunde noppi", "chhati ma peed", "saas ni auni",
        "साँस", "सांस", "सीने में दर्द", "दर्द", "एम्बुलेंस", "நெஞ்சு வலி", "மூச்சு", "বুকের ব্যথা", "শ্বাসকষ্ট", "ಎದೆ ನೋವು"
    ])
    if has_cardiac_breath and any(w in text_lower for w in ["nahi", "pain", "dard", "behosh", "vali", "betha", "novu", "noppi", "peed", "kosto", "दर्द", "नहीं"]):
        predictions.append({
            "type": "medical_emergency",
            "p": 0.96,
            "description": "Medical Emergency"
        })

    has_fire_accident = any(k in text_lower for k in [
        "aag", "fire", "cylinder", "blast", "thee", "agun", "benki", "manta", "durghatona", "vibathu", "aparadha", "hadsa", "gaddi ulati", "palti",
        "आग", "विपತ್ತು", "தீ", "আগুন", "দুর্ঘটনা", "ಬೆಂಕಿ", "ಅಪಘಾತ", "మంటలు"
    ])
    if has_fire_accident and any(w in text_lower for w in ["lag", "fire", "blast", "pidithadhu", "legeche", "bithu", "spot", "crash", "accident", "ulati", "palti", "pelindi"]):
        predictions.append({
            "type": "accident_fire",
            "p": 0.96,
            "description": "Accident & Fire Hazard"
        })

    for threat, patterns in THREAT_KEYWORDS.items():
        score = 0.0
        for pat in patterns:
            if pat in text_lower:
                score = max(score, 0.92)
            elif fuzz.partial_ratio(pat, text_lower) >= 88:
                score = max(score, 0.78)
                
        if score > 0.0 and not any(p["type"] == threat for p in predictions):
            predictions.append({
                "type": threat,
                "p": round(score, 2),
                "description": threat.replace("_", " ").title()
            })
            
    if not predictions:
        predictions.append({
            "type": "other",
            "p": 0.50,
            "description": "General Helpline Query"
        })
        
    return sorted(predictions, key=lambda x: -x["p"])

def extract_key_details(text: str) -> Dict[str, Any]:
    """Extract victim, perpetrator relationship, weapon, injury, ongoing flag, and children."""
    text_lower = text.lower()
    
    # Victim
    victim = None
    for v_key, pats in VICTIM_PATTERNS.items():
        if any(re.search(r'\b' + re.escape(p) + r'\b', text_lower) for p in pats):
            victim = v_key
            break
            
    # Perpetrator
    perp = None
    for p_key, pats in PERPETRATOR_PATTERNS.items():
        if any(re.search(r'\b' + re.escape(p) + r'\b', text_lower) for p in pats):
            perp = p_key
            break
            
    # Weapon
    weapon = None
    for w_key, pats in WEAPON_PATTERNS.items():
        if any(re.search(r'\b' + re.escape(p) + r'\b', text_lower) for p in pats):
            weapon = w_key
            break
            
    # Injury
    injury = None
    for i_key, pats in INJURY_PATTERNS.items():
        if any(re.search(r'\b' + re.escape(p) + r'\b', text_lower) for p in pats):
            injury = i_key
            break
            
    # Ongoing vs Past
    ongoing = True
    if any(k in text_lower for k in ["kal hua tha", "yesterday", "pichle hafte", "last week", "pehle bhi", "past"]):
        if not any(k in text_lower for k in ["abhi", "right now", "phir se", "again", "jaldi aao"]):
            ongoing = False
            
    # Children present
    children_present = any(k in text_lower for k in ["bacche", "baccha", "chhota", "kids", "child"])

    return {
        "victim": victim or "caller",
        "perpetrator_rel": perp,
        "weapon": weapon,
        "injury": injury,
        "ongoing": ongoing,
        "children_present": children_present,
        "time_phrase": "Current / Ongoing" if ongoing else "Past Incident"
    }

def detect_missing_information(details: Dict[str, Any], locations: List[Dict[str, Any]]) -> Tuple[List[str], Optional[str]]:
    """Identify missing critical parameters and propose a specific next question."""
    missing = []
    
    if not locations or len(locations) == 0:
        missing.append("Exact Location / Landmark")
    elif locations[0].get("confidence", 0) < 0.8:
        missing.append("Location Confirmation")
        
    if details.get("ongoing") and not details.get("perpetrator_rel") and not details.get("injury"):
        missing.append("Nature of Immediate Threat")
        
    suggested_q = None
    if "Exact Location / Landmark" in missing or "Location Confirmation" in missing:
        suggested_q = "Aap abhi kis address ya landmark par hain? (Where are you right now?)"
    elif details.get("ongoing") and not details.get("injury"):
        suggested_q = "Kya kisi ko chot aayi hai ya medical madad chahiye? (Is anyone injured?)"
    else:
        suggested_q = "Aap safe jagah par ho? Kya police bhejein? (Are you safe? Should we dispatch police?)"
        
    return missing, suggested_q
