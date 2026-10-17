"""Test covert distress signal detection, food orders, and whisper patterns."""
import pytest
from sahaay.triage.covert_detector import detect_covert_signals

def test_pizza_order_covert_signal():
    text = "hello mujhe ek large cheese pizza bhej do jaldi se"
    res = detect_covert_signals(text, text)
    assert res["covert_detected"] is True
    assert res["covert_level"] == "P1"
    assert res["safe_contact_flag"] is False
    assert res["suggested_safe_question"] is not None

def test_wrong_number_covert_signal():
    text = "sorry wrong number lag gaya... wo mera bhai room mein hai (whisper)"
    res = detect_covert_signals(text, text)
    assert res["covert_detected"] is True
    assert res["has_whisper"] is True
    assert res["safe_contact_flag"] is False

def test_benign_call_no_covert_signal():
    text = "mujhe legal aid center ka pata bata dijiye"
    res = detect_covert_signals(text, text)
    assert res["covert_detected"] is False
    assert res["safe_contact_flag"] is True
