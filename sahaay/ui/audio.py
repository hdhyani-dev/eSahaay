"""Audio utility for Sahaay Emergency CAD workstation.
Generates and plays realistic PBX emergency telephone ringtone alerts.
"""
import io
import math
import wave
import struct
import base64
from pathlib import Path
from typing import Optional

ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
RINGTONE_PATH = ASSETS_DIR / "emergency_ringtone.wav"

_CACHED_B64: Optional[str] = None
_CACHED_BYTES: Optional[bytes] = None


def generate_emergency_ringtone_bytes() -> bytes:
    """Synthesize high-clarity PBX dual-tone emergency telephone ringtone (440Hz + 480Hz)."""
    sample_rate = 22050
    duration = 2.8  # 2.8s loop cadence
    frames = []

    # Two distinct bell bursts:
    # Burst 1: 0.0s to 0.42s
    # Silence: 0.42s to 0.58s
    # Burst 2: 0.58s to 1.0s
    # Long Silence: 1.0s to 2.8s
    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        in_burst_1 = (0.0 <= t < 0.42)
        in_burst_2 = (0.58 <= t < 1.0)

        if in_burst_1 or in_burst_2:
            burst_t = t if in_burst_1 else (t - 0.58)
            burst_len = 0.42
            fade_in = min(burst_t / 0.015, 1.0)
            fade_out = min((burst_len - burst_t) / 0.020, 1.0)
            env = max(0.0, fade_in * fade_out)

            # Dual-tone CAD ring (440 Hz + 480 Hz) with warm harmonics
            s1 = math.sin(2 * math.pi * 440 * t)
            s2 = math.sin(2 * math.pi * 480 * t)
            h1 = 0.15 * math.sin(2 * math.pi * 880 * t)
            sample = (0.45 * s1 + 0.45 * s2 + h1) * env
            val = int(sample * 26000)
        else:
            val = 0
        frames.append(struct.pack("<h", val))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
    return buf.getvalue()


def get_ringtone_bytes() -> bytes:
    """Return raw bytes of emergency ringtone, from disk cache or on-the-fly synthesis."""
    global _CACHED_BYTES
    if _CACHED_BYTES is not None:
        return _CACHED_BYTES

    if RINGTONE_PATH.exists():
        try:
            with open(RINGTONE_PATH, "rb") as f:
                _CACHED_BYTES = f.read()
                return _CACHED_BYTES
        except Exception:
            pass

    # Synthesize fallback
    _CACHED_BYTES = generate_emergency_ringtone_bytes()
    try:
        ASSETS_DIR.mkdir(parents=True, exist_ok=True)
        with open(RINGTONE_PATH, "wb") as f:
            f.write(_CACHED_BYTES)
    except Exception:
        pass
    return _CACHED_BYTES


def get_ringtone_b64() -> str:
    """Return base64-encoded ringtone audio for inline data-URI embedding."""
    global _CACHED_B64
    if _CACHED_B64 is not None:
        return _CACHED_B64
    b = get_ringtone_bytes()
    _CACHED_B64 = base64.b64encode(b).decode("ascii")
    return _CACHED_B64
