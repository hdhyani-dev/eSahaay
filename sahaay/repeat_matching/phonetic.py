"""Hinglish-aware phonetic soundex and metaphone algorithm for Indian names.
Reference: Section 8.3
"""
import re

# Indian name phonetic replacement rules
PHONETIC_REPLACEMENTS = [
    (r'oo|ou', 'u'),
    (r'ee|ea|ey', 'i'),
    (r'ph', 'f'),
    (r'sh|sch|ch', 's'),
    (r'jh|zh', 'j'),
    (r'gh', 'g'),
    (r'dh', 'd'),
    (r'th', 't'),
    (r'bh', 'b'),
    (r'kh', 'k'),
    (r'w', 'v'),
    (r'y', 'i'),
    (r'z', 'j'),
    (r'ksh|x', 'ks')
]

def get_phonetic_key(name: str) -> str:
    """
    Generate phonetic soundex key tailored for Indian names.
    Examples: 'Pooja' & 'Puja' -> 'PUJA', 'Ritu' & 'Reetu' -> 'RITU'
    """
    if not name or not name.strip():
        return ""
        
    s = name.lower().strip()
    
    # 1. Apply phonetic replacements
    for pat, repl in PHONETIC_REPLACEMENTS:
        s = re.sub(pat, repl, s)
        
    # 2. Remove duplicate consecutive letters
    s = re.sub(r'(.)\1+', r'\1', s)
    
    # 3. Clean up non-alpha
    s = re.sub(r'[^a-z]', '', s)
    
    return s.upper()

def phonetic_similarity(name1: str, name2: str) -> float:
    """Compute phonetic match similarity between two caller or suspect names."""
    if not name1 or not name2:
        return 0.0
    k1 = get_phonetic_key(name1)
    k2 = get_phonetic_key(name2)
    
    if k1 == k2:
        return 1.0
    if not k1 or not k2:
        return 0.0
        
    # Levenshtein distance on phonetic keys
    from rapidfuzz import fuzz
    return fuzz.ratio(k1, k2) / 100.0
