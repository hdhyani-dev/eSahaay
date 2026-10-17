"""HMAC Keyed phone and personal identifier hashing for privacy protection.
Reference: Section 1.4, 8.3, 11.1
"""
import hmac
import hashlib
import re
from sahaay.config import settings

def clean_phone(phone: str) -> str:
    """Normalize phone number to digits only, removing country code prefixes if needed."""
    digits = re.sub(r'\D', '', phone)
    if digits.startswith("91") and len(digits) > 10:
        digits = digits[2:]
    return digits[-10:] if len(digits) >= 10 else digits

def hash_phone_hmac(phone: str) -> str:
    """Compute HMAC-SHA256 hash of telephone number using server-held secret key."""
    if not phone:
        return ""
    digits = clean_phone(phone)
    if not digits:
        return ""
    return hmac.new(
        settings.hmac_secret.encode("utf-8"),
        digits.encode("utf-8"),
        hashlib.sha256
    ).hexdigest()

def mask_phone_number(phone: str) -> str:
    """Mask telephone number for display, retaining country code and last 4 digits."""
    digits = clean_phone(phone)
    if not digits or len(digits) < 4:
        return "Unknown"
    return f"+91 98*** **{digits[-4:]}"
