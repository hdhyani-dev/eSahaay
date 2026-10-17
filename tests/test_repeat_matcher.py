"""Test repeat-complaint matching, HMAC phone privacy, and reversible links."""
import pytest
from sahaay.repeat_matching.hashing import hash_phone_hmac, mask_phone_number
from sahaay.repeat_matching.phonetic import get_phonetic_key, phonetic_similarity

def test_phone_hashing_and_masking():
    raw_phone = "+91 9876543210"
    hmac1 = hash_phone_hmac(raw_phone)
    hmac2 = hash_phone_hmac("9876543210")
    assert len(hmac1) == 64
    assert hmac1 == hmac2 # Same canonical digits
    assert "9876543210" not in hmac1
    
    masked = mask_phone_number(raw_phone)
    assert masked.endswith("3210")
    assert "***" in masked

def test_indian_name_phonetic_keys():
    # Similar sounding names must generate high similarity
    assert get_phonetic_key("Pooja") == get_phonetic_key("Puja")
    assert get_phonetic_key("Ritu") == get_phonetic_key("Reetu")
    assert phonetic_similarity("Pooja Verma", "Puja Varma") > 0.85
    assert phonetic_similarity("Amit", "Suresh") < 0.40
