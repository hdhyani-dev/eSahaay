# India-Specific Future Telephony Integration Architecture
## eSahaay Emergency Response & Triage System

> [!IMPORTANT]
> **SIMULATION BOUNDARY NOTICE**
> The current deliverable of eSahaay operates strictly in **Simulation Mode** using deterministic scenario generators and the `SimulatedCallProvider`. No live phone numbers, audio streaming, or carrier telephony are connected in this prototype. Never connect eSahaay directly to India's public emergency number 112 or any live emergency service line.

---

### 1. Recommended Indian Telephony Provider: Exotel

For future production transition and field trials in India, **Exotel** is recommended as the primary candidate telephony provider for initial architectural evaluation, subject to:
- Official commercial account registration and organizational approval.
- Telecommunications regulatory compliance and KYC verification under Department of Telecommunications (DoT) and Telecom Regulatory Authority of India (TRAI) norms.
- Current inbound virtual number (DID/toll-free) availability in Indian circles (Delhi NCR, Mumbai, etc.).
- Confirmation of low-latency Audio Media Streaming (WebSocket) capability on the intended account tier.

#### Why Exotel as the First Provider to Evaluate?
1. **Local Telecommunication Infrastructure:** Strong direct interconnects with Indian telcos (Airtel, Jio, Vi, BSNL) ensuring minimal packet loss and optimal call connect rates across tier-1, tier-2, and rural Indian circles.
2. **India Data Sovereignty & Regulations:** In-country data hosting and compliance with the Digital Personal Data Protection Act (DPDP Act, 2023) and Telecom Commercial Communications Customer Preference Regulations (TCCCPR).
3. **Programmable Voice APIs & Webhooks:** Rich webhook callbacks for call lifecycle events (`ringing`, `answered`, `terminal`, `hangup`), DTMF collection, and call recording controls.
4. **Media Streaming Support:** Low-latency bi-directional or uni-directional voice streaming via secure WebSockets (WSS).

---

### 2. End-to-End Future System Flow

```
+--------------------------------------------------------------------------------------------------+
|                                    CALLER (Phone / Mobile)                                       |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼ (Inbound Call to Authorized Test Pilot Number)
+--------------------------------------------------------------------------------------------------+
|                                EXOTEL TELEPHONY PLATFORM                                         |
|  - Virtual Pilot Number / SIP Trunking                                                           |
|  - Inbound Call Webhook (POST /telephony/exotel/incoming)                                        |
|  - Audio Forking / Real-time Media Stream over WSS                                               |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼ (Secure WebSocket Stream: 16kHz PCM audio)
+--------------------------------------------------------------------------------------------------+
|                           SECURE PYTHON WEBSOCKET & ASR BRIDGE                                   |
|  - Webhook Signature Verification (HMAC-SHA256)                                                  |
|  - Ephemeral Audio Processing (NO raw audio persisted to disk by default)                        |
|  - Streaming Speech-to-Text: Bhashini / IndicASR / Conformer / Whisper Multilingual               |
|  - Generates Incremental Transcript Events:                                                      |
|      * Partial Hypothesis (interim text, is_final=False)                                         |
|      * Final Committed Utterance (is_final=True, asr_confidence, timestamps)                     |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼ (Internal Stream / Queue / Redis Streams)
+--------------------------------------------------------------------------------------------------+
|                               HYBRID AI TRIAGE ENGINE (eSahaay NLP Core)                         |
|  - M1: Normalizer (Script ID, Hinglish Canonicalization, Variant Folding)                        |
|  - M2: Structured Fact & Location Extractor (Gazetteer & Spatial Prepositions)                   |
|  - M3: Covert-Signal & Code-Word Detector (Whisper detection, safe yes/no prompts)               |
|  - M4: Safety-First Urgency Engine (Rules Floor + Calibrated Classifier + Uncertainty Escalation)|
|  - M5: Multi-Label Service Router (Police, Medical, Shelter, Legal, Counselling)                |
|  - M6: Cautious Repeat-Complaint Matcher (HMAC Phone, Phonetic Keys, 2-Strong-Signals Rule)       |
|  - M7: Explainer & Evidence Span Highlighter                                                     |
+--------------------------------------------------------------------------------------------------+
                                                 │
                                                 ▼ (REST / WebSocket Live Updates)
+--------------------------------------------------------------------------------------------------+
|                                STREAMLIT OPERATOR WORKSTATION                                    |
|  - One-glance Triage Card (10-second decision budget)                                            |
|  - Incremental Live Transcript Feed with highlighted evidence spans                              |
|  - One-tap Confirm / Override with mandatory audit justification                                 |
|  - Location Recovery & Candidate Confirmation                                                    |
|  - Simulated & Liaison Hand-off Dispatch Management                                              |
+--------------------------------------------------------------------------------------------------+
```

---

### 3. Provider Abstraction Seam: `CallSessionProvider`

The codebase implements a strict architectural seam in `sahaay/providers/call_provider.py`:
- `CallSessionProvider` (abstract base class) defines the protocol contract.
- `SimulatedCallProvider` is the only active provider implementation in this deliverable.
- Future providers (e.g. `ExotelCallProvider`) will inherit from `CallSessionProvider` without requiring any changes to the Streamlit UI or the Hybrid Triage Engine.

```python
class CallSessionProvider(ABC):
    @abstractmethod
    def start_call(self, scenario_id: Optional[str] = None) -> Dict[str, Any]: ...
    @abstractmethod
    def answer_call(self, session_id: str) -> Dict[str, Any]: ...
    @abstractmethod
    def reject_call(self, session_id: str) -> Dict[str, Any]: ...
    @abstractmethod
    def pause_call(self, session_id: str) -> Dict[str, Any]: ...
    @abstractmethod
    def resume_call(self, session_id: str) -> Dict[str, Any]: ...
    @abstractmethod
    def end_call(self, session_id: str) -> Dict[str, Any]: ...
    @abstractmethod
    def get_next_transcript_event(self, session_id: str) -> Optional[TranscriptEvent]: ...
```

---

### 4. Technical Requirements for Future Adapter Implementation

1. **Authentication & Webhook Validation:**
   - Verify incoming webhook signatures using HMAC-SHA256 and the provider's token.
   - Reject untrusted or unauthenticated requests with HTTP 401.

2. **Session Isolation:**
   - Every active call must have a unique `call_id` and isolated state. No cross-session data leakage.

3. **Partial vs. Final Transcript Segments:**
   - Streaming ASR emits interim tokens (`is_final=False`) for operator preview.
   - Incremental triage re-computation is triggered upon final committed phrases (`is_final=True`) to maintain sub-second response times without UI thrashing.

4. **Privacy & Data Protection by Design (DPDP Act, 2023):**
   - **No Raw Audio Storage by Default:** Audio is streamed ephemerally through RAM buffer to the speech recognizer and discarded immediately.
   - **Explicit Consent:** Call recording is only activated if configured under explicit legal and helpline policy consent protocols.
   - **PII Protection:** Phone numbers are keyed-hashed using server-side HMAC-SHA256 (`sahaay/repeat_matching/hashing.py`) and masked (`+91 98*** **3210`) in logs and UI.

5. **Graceful Disconnection & Fallbacks:**
   - If the telephony media stream drops or delays exceed 3.0 seconds, the system alerts the operator with an explicit `ASR_DELAY` warning and maintains the highest safety-floor triage level.
