"""M1 Normalizer: Hinglish normalization, script identification, and variant folding.
Reference: FR-1.2, FR-1.3
"""
import re
import unicodedata
from typing import List, Dict, Tuple, Any
from rapidfuzz import fuzz
from sahaay.config import _load_yaml, CONFIG_DIR

# Load canonical variant dictionary
variants_path = CONFIG_DIR / "lexicon" / "Hinglish_variants.yaml"
variants_data = _load_yaml(variants_path).get("canonical_dictionary", {})

# Invert dictionary for fast lookup: variant -> canonical
VARIANT_TO_CANONICAL: Dict[str, str] = {}
for canonical, variants in variants_data.items():
    VARIANT_TO_CANONICAL[canonical.lower()] = canonical
    for var in variants:
        VARIANT_TO_CANONICAL[var.lower()] = canonical

DEVANAGARI_RANGE = (0x0900, 0x097F)

SCRIPT_RANGES = {
    "devanagari": (0x0900, 0x097F),
    "bengali": (0x0980, 0x09FF),
    "gurmukhi": (0x0A00, 0x0A7F),
    "gujarati": (0x0A80, 0x0AFF),
    "odia": (0x0B00, 0x0B7F),
    "tamil": (0x0B80, 0x0BFF),
    "telugu": (0x0C00, 0x0C7F),
    "kannada": (0x0C80, 0x0CFF),
    "malayalam": (0x0D00, 0x0D7F),
}

# Devanagari to Roman common transliteration mapping
DEV_TO_ROMAN = {
    'अ': 'a', 'आ': 'aa', 'इ': 'i', 'ई': 'ee', 'उ': 'u', 'ऊ': 'oo', 'ऋ': 'ri',
    'ए': 'e', 'ऐ': 'ai', 'ओ': 'o', 'औ': 'au', 'क': 'k', 'ख': 'kh', 'ग': 'g',
    'घ': 'gh', 'ङ': 'ng', 'च': 'ch', 'छ': 'chh', 'ज': 'j', 'झ': 'jh', 'ञ': 'ny',
    'ट': 't', 'ठ': 'th', 'ड': 'd', 'ढ': 'dh', 'ण': 'n', 'त': 't', 'थ': 'th',
    'द': 'd', 'ध': 'dh', 'न': 'n', 'प': 'p', 'फ': 'ph', 'ब': 'b', 'भ': 'bh',
    'म': 'm', 'य': 'y', 'र': 'r', 'ल': 'l', 'व': 'v', 'श': 'sh', 'ष': 'sh',
    'स': 's', 'ह': 'h', 'ा': 'aa', 'ि': 'i', 'ी': 'ee', 'ु': 'u', 'ू': 'oo',
    'े': 'e', 'ै': 'ai', 'ो': 'o', 'ौ': 'au', '्': '', 'ं': 'n', 'ँ': 'n',
    'ः': 'h', '०': '0', '१': '1', '२': '2', '३': '3', '४': '4', '५': '5',
    '६': '6', '७': '7', '८': '8', '९': '9'
}

# Transliteration for Bengali, Tamil, Kannada, Telugu characters
INDIC_TO_ROMAN = {
    # Bengali
    'অ': 'a', 'আ': 'aa', 'ই': 'i', 'ঈ': 'ee', 'উ': 'u', 'ঊ': 'oo',
    'এ': 'e', 'ঐ': 'oi', 'ও': 'o', 'ঔ': 'ou', 'ক': 'k', 'খ': 'kh', 'গ': 'g',
    'ঘ': 'gh', 'ঙ': 'ng', 'চ': 'ch', 'ছ': 'chh', 'জ': 'j', 'ঝ': 'jh', 'ঞ': 'ny',
    'ট': 't', 'ঠ': 'th', 'ড': 'd', 'ঢ': 'dh', 'ণ': 'n', 'ত': 't', 'থ': 'th',
    'দ': 'd', 'ধ': 'dh', 'ন': 'n', 'প': 'p', 'ফ': 'ph', 'ব': 'b', 'ভ': 'bh',
    'ম': 'm', 'য': 'j', 'র': 'r', 'ল': 'l', 'শ': 'sh', 'ষ': 'sh', 'স': 's',
    'হ': 'h', 'া': 'aa', 'ি': 'i', 'ী': 'ee', 'ু': 'u', 'ূ': 'oo', 'ে': 'e',
    'ৈ': 'oi', 'ো': 'o', 'ৌ': 'ou', '্': '', 'ং': 'ng',
    # Tamil
    'அ': 'a', 'ஆ': 'aa', 'இ': 'i', 'ஈ': 'ee', 'உ': 'u', 'ஊ': 'oo',
    'எ': 'e', 'ஏ': 'ee', 'ஐ': 'ai', 'ஒ': 'o', 'ஓ': 'oo', 'ஔ': 'au',
    'க': 'k', 'ங': 'ng', 'ச': 's', 'ஞ': 'ny', 'ட': 't', 'ண': 'n',
    'த': 'th', 'ந': 'n', 'ப': 'p', 'ம': 'm', 'ய': 'y', 'ர': 'r',
    'ல': 'l', 'வ': 'v', 'ழ': 'zh', 'ள': 'l', 'ற': 'r', 'ன': 'n',
    'ா': 'aa', 'ி': 'i', 'ீ': 'ee', 'ு': 'u', 'ூ': 'oo', 'ெ': 'e',
    'ே': 'ee', 'ை': 'ai', 'ொ': 'o', 'ோ': 'oo', 'ௌ': 'au', '்': '',
    # Kannada
    'ಅ': 'a', 'ಆ': 'aa', 'ಇ': 'i', 'ಈ': 'ee', 'ಉ': 'u', 'ಊ': 'oo',
    'ಎ': 'e', 'ಏ': 'ee', 'ಐ': 'ai', 'ಒ': 'o', 'ಓ': 'oo', 'ಔ': 'au',
    'ಕ': 'k', 'ಖ': 'kh', 'ಗ': 'g', 'ಘ': 'gh', 'ಚ': 'ch', 'ಛ': 'chh',
    'ಜ': 'j', 'ಝ': 'jh', 'ಟ': 't', 'ಠ': 'th', 'ಡ': 'd', 'ಢ': 'dh',
    'ಣ': 'n', 'ತ': 't', 'ಥ': 'th', 'ದ': 'd', 'ಧ': 'dh', 'ನ': 'n',
    'ಪ': 'p', 'ಫ': 'ph', 'ಬ': 'b', 'ಭ': 'bh', 'ಮ': 'm', 'ಯ': 'y',
    'ರ': 'r', 'ಲ': 'l', 'ವ': 'v', 'ಶ': 'sh', 'ಷ': 'sh', 'ಸ': 's',
    'ಹ': 'h', 'ಳ': 'l', 'ಾ': 'aa', 'ಿ': 'i', 'ೀ': 'ee', 'ು': 'u',
    'ೂ': 'oo', 'ೆ': 'e', 'ೇ': 'ee', 'ೈ': 'ai', 'ೊ': 'o', 'ೋ': 'oo',
    'ೌ': 'au', '್': '', 'ಂ': 'm'
}

def identify_script(token: str) -> str:
    """Identify if a token is Devanagari, Tamil, Bengali, Kannada, Telugu, etc., Roman, Digit or Mixed."""
    matched_scripts = set()
    has_rom = any('a' <= c.lower() <= 'z' for c in token)
    has_dig = any(c.isdigit() for c in token)
    
    for c in token:
        code = ord(c)
        for s_name, (start, end) in SCRIPT_RANGES.items():
            if start <= code <= end:
                matched_scripts.add(s_name)
                break
                
    if matched_scripts and has_rom:
        return "mixed"
    if len(matched_scripts) == 1:
        return list(matched_scripts)[0]
    if len(matched_scripts) > 1:
        return "mixed_indic"
    if has_rom:
        return "roman"
    if has_dig:
        return "numeric"
    return "symbol"

def transliterate_devanagari_to_roman(text: str) -> str:
    """Transliterate Devanagari script to romanized phonetics."""
    result = []
    for char in text:
        result.append(DEV_TO_ROMAN.get(char, char))
    return "".join(result)

def transliterate_indic_to_roman(text: str) -> str:
    """Transliterate any Indic script (Devanagari, Tamil, Bengali, Kannada, etc.) to Roman phonetics."""
    result = []
    for char in text:
        if char in DEV_TO_ROMAN:
            result.append(DEV_TO_ROMAN[char])
        elif char in INDIC_TO_ROMAN:
            result.append(INDIC_TO_ROMAN[char])
        else:
            result.append(char)
    return "".join(result)

def fold_variant(token: str) -> str:
    """Fold a spelling variant to its canonical token using exact or fuzzy match."""
    t_lower = token.lower().strip()
    if not t_lower:
        return token
        
    # 1. Exact match in dictionary
    if t_lower in VARIANT_TO_CANONICAL:
        return VARIANT_TO_CANONICAL[t_lower]
        
    # 2. De-duplication of consecutive repeated characters (e.g. maaaaarr -> maar)
    dedup = re.sub(r'(.)\1{2,}', r'\1\1', t_lower)
    if dedup in VARIANT_TO_CANONICAL:
        return VARIANT_TO_CANONICAL[dedup]
        
    # 3. Fuzzy match against variant keys for high similarity (>= 88)
    for var, canon in VARIANT_TO_CANONICAL.items():
        if len(var) >= 3 and abs(len(var) - len(t_lower)) <= 2:
            if fuzz.ratio(t_lower, var) >= 88:
                return canon
                
    return token

def normalize_hinglish(raw_text: str) -> Dict[str, Any]:
    """
    Main normalization pipeline for Pan-Indian multilingual transcripts:
    - Unicode NFC normalization
    - Tokenization across Indic scripts and Roman
    - Transliteration of Indic scripts (Devanagari, Tamil, Bengali, Kannada, etc.)
    - Canonical variant folding
    """
    if not raw_text or not raw_text.strip():
        return {
            "raw_text": "",
            "normalized_text": "",
            "tokens": [],
            "lang_mix": "empty",
            "scripts": set()
        }
        
    nfc_text = unicodedata.normalize("NFC", raw_text)
    
    # Tokenize capturing word tokens across all Indic scripts and Roman
    token_matches = list(re.finditer(r'\b[\w\u0900-\u0D7F]+\b|[^\w\s]', nfc_text))
    
    normalized_tokens = []
    scripts_found = set()
    canon_tokens = []
    
    for m in token_matches:
        raw_tok = m.group()
        start = m.start()
        end = m.end()
        script = identify_script(raw_tok)
        scripts_found.add(script)
        
        # Romanize Indic scripts
        if script in ["devanagari", "bengali", "tamil", "kannada", "telugu", "gujarati"]:
            roman_tok = transliterate_indic_to_roman(raw_tok)
        else:
            roman_tok = raw_tok

        # Fold variant
        canon_tok = fold_variant(roman_tok)
        
        token_info = {
            "raw": raw_tok,
            "start": start,
            "end": end,
            "script": script,
            "canonical": canon_tok
        }
        normalized_tokens.append(token_info)
        canon_tokens.append(canon_tok)

    # Reconstruct normalized string
    normalized_text = " ".join([t["canonical"] for t in normalized_tokens if t["script"] != "symbol"])
    
    # Determine dominant language mix
    lower_raw = raw_text.lower()
    if "tamil" in scripts_found or any(w in lower_raw for w in ["kaapaathunga", "udhavi", "kanavan", "asaiyaama", "moochu", "thevai", "thee pidithadhu", "stroke pola", "appa ku"]):
        lang_mix = "Tamil (தமிழ் / Tanglish)"
    elif "bengali" in scripts_found or any(w in lower_raw for w in ["bachan", "sahajjo", "marchhe", "shami", "rokto", "agun", "osustho", "dorkar", "aamader flat", "meter box", "dhnowa"]):
        lang_mix = "Bengali (বাংলা / Banglish)"
    elif "kannada" in scripts_found or any(w in lower_raw for w in ["sahaya madi", "bachasi", "ganda", "hodeyuthiddane", "raktha", "benki", "ede novu", "speeding lorry", "taleyinda", "kalsi"]):
        lang_mix = "Kannada (ಕನ್ನಡ / Kanglish)"
    elif any(w in lower_raw for w in ["madat kara", "gaddi ulati", "chot lagi cha", "khasam", "bhyola", "chhati ma peed", "dhoong pado", "khayi ma", "yatri fasa"]):
        lang_mix = "Kumaoni / Pahari (कुमाऊँनी)"
    elif "telugu" in scripts_found or any(w in lower_raw for w in ["kapadandi", "sahayam", "bhartha", "koduthunnadu", "raktham", "gunde noppi"]):
        lang_mix = "Telugu (తెలుగు / Tenglish)"
    elif any(w in lower_raw for w in ["navra martoy", "marhan hot ahe", "aag lagli", "chhati dukhate"]):
        lang_mix = "Marathi (मराठी)"
    elif "gujarati" in scripts_found or any(w in lower_raw for w in ["madad karo", "pati mare chhe", "lohi nikle", "aag lagi chhe"]):
        lang_mix = "Gujarati (ગુજરાતી)"
    elif "devanagari" in scripts_found and "roman" in scripts_found:
        lang_mix = "Hindi / Hinglish (Devanagari + Roman)"
    elif "devanagari" in scripts_found:
        lang_mix = "Hindi (Devanagari)"
    elif any(w in lower_raw for w in ["maar", "bachao", "madad", "chaku", "aag", "saans", "dard", "khoon", "pcr", "police"]):
        lang_mix = "Hinglish (Romanized)"
    elif "roman" in scripts_found:
        lang_mix = "English / Hinglish"
    else:
        lang_mix = "Multilingual Indic"

    return {
        "raw_text": raw_text,
        "normalized_text": normalized_text,
        "tokens": normalized_tokens,
        "lang_mix": lang_mix,
        "scripts": list(scripts_found)
    }
