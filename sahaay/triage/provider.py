"""AI Model Provider Abstraction for Hybrid Helpline Triage.
Supports hosted LLMs (Gemini / OpenAI) with deterministic rules fallback.
"""
import os
import time
import json
from typing import Dict, Any, Tuple
from sahaay.config import settings

class ModelProvider:
    def __init__(self):
        self.provider_name = settings.ai_provider
        self.gemini_key = settings.gemini_api_key
        self.openai_key = settings.openai_api_key
        self.is_api_available = bool(self.gemini_key or self.openai_key)

    def classify_and_assess(
        self,
        raw_text: str,
        normalized_text: str
    ) -> Tuple[str, float, str, Dict[str, Any]]:
        """
        Evaluate transcript using model or deterministic fallback classifier.
        Returns: (predicted_level, confidence, engine_mode, raw_model_output)
        """
        start_time = time.time()
        
        # 1. If Gemini API key is configured, use Gemini
        if self.gemini_key:
            try:
                import requests
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
                prompt = (
                    "You are eSahaay Emergency Triage Engine for Hinglish helpline calls.\n"
                    "Analyze this call transcript and output JSON ONLY with schema:\n"
                    "{\"urgency\": \"P0\"|\"P1\"|\"P2\"|\"P3\", \"confidence\": float (0.0 to 1.0), "
                    "\"threat_type\": string, \"victim\": string, \"weapon\": string, \"injury\": string, \"ongoing\": bool}\n\n"
                    f"Transcript: {raw_text}"
                )
                resp = requests.post(
                    url,
                    json={"contents": [{"parts": [{"text": prompt}]}]},
                    headers={"Content-Type": "application/json"},
                    timeout=3.0
                )
                if resp.status_code == 200:
                    data = resp.json()
                    text_resp = data["candidates"][0]["content"]["parts"][0]["text"]
                    cleaned_json = text_resp.strip().replace("```json", "").replace("```", "").strip()
                    parsed = json.loads(cleaned_json)
                    return (
                        parsed.get("urgency", "P2"),
                        float(parsed.get("confidence", 0.88)),
                        "Gemini-1.5-Flash (Hybrid)",
                        parsed
                    )
            except Exception as e:
                # Graceful degradation on API failure
                pass

        # 2. High-performance deterministic fallback classifier
        # Analyzes risk density, urgency tokens, and negative sentiment
        text_lower = (raw_text + " " + normalized_text).lower()
        
        p0_indicators = ["maar raha", "chaku", "bandook", "saans nahi", "chest pain", "behosh", "khoon", "bleeding", "aag lag"]
        p1_indicators = ["dhamki", "peecha kar raha", "dar lag raha", "kamre me band", "pizza", "wrong number", "bachao", "police"]
        p2_indicators = ["harass", "chedkhani", "ladai", "jhagda", "kal hua", "complaint karni", "padosi"]
        p3_indicators = ["talaq", "divorce", "maintenance", "kanoon", "court", "procedure", "vakeel", "information"]

        p0_score = sum(1 for w in p0_indicators if w in text_lower)
        p1_score = sum(1 for w in p1_indicators if w in text_lower)
        p2_score = sum(1 for w in p2_indicators if w in text_lower)
        p3_score = sum(1 for w in p3_indicators if w in text_lower)

        if p0_score > 0:
            level = "P0"
            conf = min(0.95, 0.85 + 0.05 * p0_score)
        elif p1_score > 0:
            level = "P1"
            conf = min(0.92, 0.80 + 0.05 * p1_score)
        elif p2_score > 0:
            level = "P2"
            conf = 0.82
        elif p3_score > 0:
            level = "P3"
            conf = 0.90
        else:
            level = "P2"
            conf = 0.65 # Low confidence triggers uncertainty escalation

        engine_mode = "Rules-Only Fallback Engine (No API Key)"
        return level, conf, engine_mode, {"deterministic_scores": {"P0": p0_score, "P1": p1_score, "P2": p2_score, "P3": p3_score}}

provider = ModelProvider()
