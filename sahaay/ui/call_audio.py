"""Audio utility for emergency call recording playback in eSahaay CAD."""
import io
import math
import wave
import struct
import base64

_RECORDING_CACHE = {}

def generate_call_recording_bytes(incident_id: str = "INC-1042") -> bytes:
    """Synthesize simulated 16kHz emergency call recording with PBX radio burst and voiceband cadence."""
    sample_rate = 16000
    duration = 4.5
    frames = []

    seed_val = sum(ord(c) for c in str(incident_id))
    base_pitch = 240 + (seed_val % 120)

    for i in range(int(sample_rate * duration)):
        t = i / sample_rate
        if 0.0 <= t < 0.12:
            f = 850 + 600 * math.sin(2 * math.pi * 35 * t)
            sample = 0.35 * math.sin(2 * math.pi * f * t)
        elif 0.15 <= t < 4.2:
            cadence = math.sin(2 * math.pi * 3.8 * t) * math.sin(2 * math.pi * 1.5 * t)
            speech_env = max(0.0, cadence) ** 1.5
            f1 = base_pitch
            f2 = f1 * 2.1
            f3 = f1 * 3.4
            speech = (
                0.45 * math.sin(2 * math.pi * f1 * t) +
                0.30 * math.sin(2 * math.pi * f2 * t) +
                0.15 * math.sin(2 * math.pi * f3 * t)
            ) * speech_env
            line_hum = 0.03 * math.sin(2 * math.pi * 50 * t)
            sample = speech * 0.75 + line_hum
        elif 4.25 <= t < 4.35:
            click_env = math.exp(-35 * (t - 4.25))
            sample = 0.4 * math.sin(2 * math.pi * 600 * t) * click_env
        else:
            sample = 0.0
        val = int(max(-1.0, min(1.0, sample)) * 24000)
        frames.append(struct.pack("<h", val))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(frames))
    return buf.getvalue()

def get_call_recording_b64(incident_id: str = "INC-1042") -> str:
    """Return base64-encoded audio for emergency call playback."""
    if incident_id not in _RECORDING_CACHE:
        raw_b = generate_call_recording_bytes(incident_id)
        _RECORDING_CACHE[incident_id] = base64.b64encode(raw_b).decode("ascii")
    return _RECORDING_CACHE[incident_id]
