"""Tests for real-time Pan-Indian to English translation engine."""
from sahaay.triage.translate import translate_to_english

def test_translate_tamil_to_english():
    ta_text = "En appa ku thideernu oru pakkam kai kaal asaiyaama poiduchi, vaai saanjiduchi!"
    trans = translate_to_english(ta_text)
    assert "father" in trans.lower()
    assert "movement" in trans.lower() or "drooped" in trans.lower()

def test_translate_bengali_to_english():
    bn_text = "Aamader flat er ground floor electrical meter box theke bishal agun legeche!"
    trans = translate_to_english(bn_text)
    assert "fire" in trans.lower()
    assert "meter box" in trans.lower()

def test_translate_kannada_to_english():
    kn_text = "Ondhu speeding lorry bike ge guddhittu nilladhe hodithu, rider biddu biddane!"
    trans = translate_to_english(kn_text)
    assert "speeding" in trans.lower() or "truck" in trans.lower() or "motorcycle" in trans.lower()

def test_translate_kumaoni_to_english():
    ku_text = "Pahad bata dhoong pado aur passenger gaddi divider todi ber khayi ma ulti gayi!"
    trans = translate_to_english(ku_text)
    assert "passenger vehicle" in trans.lower() or "boulders" in trans.lower() or "divider" in trans.lower()

def test_translate_hinglish_to_english():
    hi_text = "pati chaku dikha kar maar raha hai, Sector 14 Rohini gali number 3, bacche ro rahe hain!"
    trans = translate_to_english(hi_text)
    assert "husband" in trans.lower()
    assert "knife" in trans.lower()
    assert "children" in trans.lower()

