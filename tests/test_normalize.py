"""Test Hinglish normalization, Devanagari transliteration, and variant folding."""
import pytest
from sahaay.triage.normalize import (
    identify_script,
    transliterate_devanagari_to_roman,
    fold_variant,
    normalize_hinglish
)

def test_script_identification():
    assert identify_script("bachao") == "roman"
    assert identify_script("बचाओ") == "devanagari"
    assert identify_script("110085") == "numeric"

def test_devanagari_transliteration():
    dev = "मदद"
    roman = transliterate_devanagari_to_roman(dev)
    assert "m" in roman and "d" in roman

def test_spelling_variant_folding():
    # FR-1.2: Variant list resolves to same canonical token (maar / mar / maara)
    assert fold_variant("maar") == "maar"
    assert fold_variant("mar") == "maar"
    assert fold_variant("maara") == "maar"
    assert fold_variant("peet") == "maar"
    assert fold_variant("khun") == "khoon"
    assert fold_variant("chaaku") == "chaku"
    assert fold_variant("sans") == "saans"

def test_normalize_hinglish_pipeline():
    raw = "bhaiya jaldi aao, pati mar rha hai"
    norm = normalize_hinglish(raw)
    assert norm["lang_mix"] != "empty"
    assert "maar" in norm["normalized_text"]
    assert len(norm["tokens"]) > 0

def test_multilingual_indic_scripts():
    assert identify_script("காப்பாத்துங்க") == "tamil"
    assert identify_script("বাঁচান") == "bengali"
    assert identify_script("ಸಹಾಯ") == "kannada"

def test_multilingual_pan_indian_detection():
    # Tamil Tanglish
    norm_ta = normalize_hinglish("kaapaathunga kanavan adikkiraanga ratham thevai")
    assert "Tamil" in norm_ta["lang_mix"]

    # Bengali Banglish
    norm_bn = normalize_hinglish("bachan please shami marchhe rokto porche")
    assert "Bengali" in norm_bn["lang_mix"]

    # Kannada Kanglish
    norm_kn = normalize_hinglish("sahaya madi ganda hodeyuthiddane raktha harithide")
    assert "Kannada" in norm_kn["lang_mix"]

    # Kumaoni Pahari
    norm_ku = normalize_hinglish("madat kara khasam maran laagi gaddi ulati chot lagi cha")
    assert "Kumaoni" in norm_ku["lang_mix"]

