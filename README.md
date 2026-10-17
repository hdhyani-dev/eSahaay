# eSahaay — Emergency Response & Triage System

> **Problem Statement 3 (Hack@BVP 8.0):** *Ten Seconds to Read a Call: Helpline Triage in Hinglish*  
> **Tagline:** *Faster response. Safer communities.*

---

## 🛡️ Executive Summary & Product Mission

In emergency helplines (112, 181, 108), callers often communicate in **noisy, code-mixed Hindi, English, and Hinglish**, speak in fragmented whispers, or use covert pretexts because a perpetrator is in the room. An operator has roughly **ten seconds** to interpret the call, evaluate urgency, extract location and incident facts, and route cases to police, medical, shelter, or legal assistance.

**eSahaay** is an operator co-pilot built to guarantee that **emergencies are never silently downgraded**. By fusing **multilingual NLP reasoning** with **deterministic safety rules**, eSahaay provides human call-takers with an explainable, one-glance **Triage Card** within seconds.

---

## 🔒 Mandatory Call-Mode Boundary: Simulation Only

> [!IMPORTANT]
> **SIMULATION-ONLY ARCHITECTURAL BOUNDARY**
> - eSahaay is a hackathon prototype running in a local workstation environment.
> - **All calls, transcripts, audio streams, responder units, ETAs, and dispatch operations are strictly simulated.**
> - The application operates completely **offline** without telephony credentials, phone numbers, or paid external LLM keys.
> - The application never activates the browser microphone, dials real numbers, or connects to India's national emergency number 112.

### Provider Abstraction Seam (`CallSessionProvider`)
To ensure future-readiness without compromising local isolation:
- `sahaay/providers/call_provider.py` establishes an abstract interface (`CallSessionProvider`).
- `SimulatedCallProvider` is the active provider, streaming deterministic scenario event queues with partial interim hypotheses and committed final segments.
- Future providers (e.g. Exotel) plug directly into this abstraction without touching UI or triage logic.

---

## 🇮🇳 India-Specific Future Telephony Recommendation

For production deployment and field pilots across Indian helpline centers:

### Recommended Provider to Evaluate: **Exotel**
- **Evaluation Criteria:** Indian telecom licensing, DoT/TRAI regulatory adherence, commercial account approval, and native low-latency WebSocket audio media streaming.
- **Why Exotel First:** Direct tier-1 interconnects with Airtel, Jio, Vi, and BSNL; in-country data residency complying with the **Digital Personal Data Protection Act (DPDP Act, 2023)**; and mature webhook callbacks for call lifecycle tracking.

### Proposed Future End-to-End Pipeline
```
Inbound Pilot Number → Exotel Telephony Platform → Secure Python WebSocket Service 
  → Streaming Multilingual ASR (IndicASR / Conformer / Bhashini) 
  → Hybrid AI Triage Engine (M1..M7) → Streamlit Operator Workstation
```
*Full technical details are documented in [`docs/telephony_architecture.md`](docs/telephony_architecture.md).*

---

## ✨ Key Capabilities & Architectural Highlights

1. **Sub-3 Second Hybrid Triage Pipeline (M1 — M7):**
   - **M1 Normalizer:** Script identification (Devanagari, Roman, mixed), transliteration, and spelling-variant folding (`maar`/`mar`/`maara`).
   - **M2 Extractor:** Structured entity extraction (victim, perpetrator, weapon, injury, ongoing status) and candidate location parsing.
   - **M3 Covert Detector:** Identifies disguised calls (pizza orders, doctor queries, wrong-number pretexts) and enforces a "DO NOT CALL BACK" flag.
   - **M4 Urgency Engine:** Asymmetric max-risk fusion with deterministic rules floor; low confidence or missing location on $\ge P1$ automatically escalates priority and sets the `VERIFY` banner.
   - **M5 Router:** Multi-label service routing (Police, Medical, Shelter, Legal, Counselling) ordered by time criticality.
   - **M6 Repeat Matcher:** Conservative 2-strong-signals rule over keyed HMAC-SHA256 phone hashes, phonetic name keys, and locality tokens.
   - **M7 Explainer:** Highlights exact evidence spans in the caller's own words with rule IDs.

2. **Full Browser-Based Operator Phone Simulator:**
   - Ringing alert card with caller phone, scenario title, and Answer/Reject controls.
   - Active-call timer (MM:SS) and connection indicator.
   - Chronological transcript stream clearly distinguishing **partial interim hypotheses** from **final committed text**.
   - Playback controls: Step / Next Chunk, Fast-Forward (Stream All), Pause, Resume, End Call, and Save Incident.

3. **Dedicated Location Recovery Workflow (Section 6.H):**
   - Surfaces incidents with missing or uncertain locations.
   - Ranks candidate matches against the Delhi NCR gazetteer with coordinates and confidence.
   - Operator candidate confirmation and rejection controls.
   - Manual search box for gazetteer landmarks, metro stations, and pincodes.
   - Targeted clarification question prompts.

4. **Simulated Dispatch State Machine (Section 6.F):**
   - Deterministic status lifecycle: `Available → Assigned → Dispatched → Acknowledged → En Route → Arrived → Completed`.
   - Real-time road distance and ETA calculation using Haversine formulas.
   - Support for cancellation and unit return to base.

5. **Safety-First Evaluation Dashboard & Hidden-Set Mode:**
   - Empirical Urgent Recall with **95% Bootstrap Confidence Intervals**.
   - Severe under-triage tracking (<0.5% target) and routing macro-F1.
   - Confusion matrix and downloadable HTML evaluation report.
   - **Hidden-Set Evaluation Mode:** Generates competition submission predictions without exposing ground-truth labels.

6. **UN Sustainable Development Goals (SDG) Board:**
   - De-identified aggregate outcomes mapped to **SDG 5** (Gender Equality), **SDG 16** (Peace & Justice), **SDG 10** (Reduced Inequalities), and **SDG 9** (Innovation).
   - Enforces differential privacy with cell size suppression (<3 hidden).

---

## 🎨 Public-Sector Visual Design System

Implemented using a restrained, high-contrast palette:

| Element | Color Role | Hex Code |
|---|---|---|
| Primary Navy | Header & Brand Accent | `#173B57` |
| Secondary Blue | Information & Links | `#286A8A` |
| Critical Red | P0 Critical Urgency & Pulsing Ring | `#B42318` |
| Priority Amber | P1 High Urgency & Warnings | `#A15C00` |
| Success Green | P3 Low Urgency & Online State | `#187347` |
| Page Background | Workplace Neutral | `#F3F5F7` |
| Panel Background | White Clean Cards | `#FFFFFF` |
| Primary Text | Charcoal Navy | `#253445` |
| Secondary Text | Slate Metadata | `#526171` |
| Borders | Subtle Boundary Lines | `#E8EDF2` |

---

## 🔑 Demo Accounts & Role-Based Access Control (RBAC)

The system supports 6 distinct roles:

| Role | Employee ID | Password | Key Permissions |
|---|---|---|---|
| **Call-taker / Operator** | `OP1042` | `operator123` | Live Triage Console, Softphone Simulator, Dispatch, Location Recovery |
| **Shift Supervisor** | `SUP201` | `super123` | Repeat Review, Link Approvals/Undos, Evaluation Dashboard |
| **Responder Liaison** | `RES305` | `police123` | Assigned Dispatches, Masked Transcripts |
| **Helpline Linguist** | `LIN402` | `linguist123` | Lexicon Manager, Code Word Curation, Simulator Workbench |
| **System Administrator** | `ADM901` | `admin123` | User Management, Threshold Governance, Audit Log, Demo Reset |
| **Judge / Evaluator** | `JUDGE01` | `demo123` | Full Read-Only Inspection, Benchmark Evaluation, Hidden-Set Export |

---

## 🚀 Installation & Local Execution

### 1. Prerequisites
- Python 3.10 or 3.11 installed locally.

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
```bash
python scripts/seed_demo.py
```

### 4. Run the Streamlit Application
```bash
python -m streamlit run app.py
```
Open your browser at `http://localhost:8501`.

---

## 🧪 Automated Testing

Run the full pytest suite (37 passing automated tests):
```bash
python -m pytest tests
```

### Test Coverage Summary:
- `tests/test_safety_floor.py`: Rules floor downgrade prevention, uncertainty escalation, short evasive call safety.
- `tests/test_routing_and_priority.py`: All priority levels (P0-P3), Devanagari script, Roman Hinglish, multi-label service order.
- `tests/test_covert.py`: Pizza order, wrong-number pretext, whispered calls, safe contact flags.
- `tests/test_repeat_matcher_false_positives.py`: 2-strong-signals rule, name-alone false merge prevention, reversible unlinking.
- `tests/test_call_provider.py`: Softphone lifecycle, streaming partial/final events, session isolation, noise resilience.
- `tests/test_dispatch_state_machine.py`: Full lifecycle transitions, cancellation, Haversine ETAs.
- `tests/test_location_recovery.py`: Gazetteer matching, landmark lookups, candidate confirmation.
- `tests/test_audit_and_persistence.py`: Immutable audit logging, role permissions matrix, DB persistence.
- `tests/test_normalize.py`: NFC normalization, Devanagari script detection, variant folding.
- `tests/test_evaluation.py`: Bootstrap confidence intervals and hidden-set protocol execution.

---

## 🎬 3-Minute Demonstration Script for Judges

1. **Mission & Checklist:** Open `http://localhost:8501`. Start on the **PS3 Mission & Checklist** page (`/ps3`). Observe the 6 core problem statement requirements mapped to the prototype screens.
2. **Active P0 Emergency:** Open **Live Triage Console** (`/triage`). Trigger Scenario 1 (*Active Domestic Violence P0*). Click **Answer Call**. Step through chunks; observe real-time Triage Card updates, P0 Critical chip, and highlighted evidence spans in caller's own words. Click **Confirm Priority**.
3. **Covert Call & Code Words:** In Live Triage, select Scenario 2 (*Covert Pizza Order P1*). Answer call. Observe:
   - Urgency raised to P1 with `VERIFY` banner.
   - Safe contact flag forced to **FALSE (DO NOT CALL BACK)**.
   - Prompt suggests safe yes/no question (*"Are you in immediate danger? Answer with Yes or No only."*).
4. **Location Recovery:** Navigate to **Location Recovery** (`/location_recovery`). Select an incident with missing coordinates. Show candidate gazetteer matches and manual landmark search (*"Rohini Sector 14"*). Confirm location; observe confidence updating to 100% and audit entry created.
5. **Cautious Repeat Matching:** Open **Repeat Review** (`/repeats`). Review candidate matches for a repeat stalking complaint. Highlight the **2-strong-signals rule** preventing false merges. Approve the link, then demonstrate one-click reversible undo.
6. **Simulated Dispatch:** Open **Dispatch** (`/dispatch`). Assign an available ambulance/police unit. Click **Advance State** to walk through `Dispatched → Acknowledged → En Route → Arrived`.
7. **Evaluation & Hidden Set:** Open **Evaluation Dashboard** (`/eval`). Inspect the validation benchmark (Urgent Recall $\ge 98\%$, Severe Under-Triage $< 0.5\%$, Routing Macro-F1 $\ge 0.85$, confusion matrix). Switch to the **Hidden-Set Protocol** tab and download the submission JSON file.
8. **Admin & Demo Reset:** Open **Administration & Audit** (`/admin`). Review the append-only audit log. Demonstrate the **Demo Reset** button to cleanly reset the database.

---

## 📁 Repository Structure

```
├── app.py                      # Main Streamlit router and 14 integrated page controllers
├── requirements.txt            # Python dependencies (Streamlit, SQLAlchemy, Pydantic, RapidFuzz, etc.)
├── Dockerfile                  # Container definition for portable deployment
├── run_sahaay.bat / .ps1       # Convenience launch scripts
├── sahaay/
│   ├── config.py               # Pydantic settings and YAML loaders
│   ├── database.py             # SQLAlchemy engine and session management
│   ├── models.py               # Database entities (Incident, TriageAssessment, ResponseUnit, etc.)
│   ├── auth.py                 # Bcrypt password hashing and authentication
│   ├── permissions.py          # RBAC permission matrix and page access
│   ├── audit.py                # Append-only immutable audit event logger
│   ├── schemas.py              # Pydantic validation schemas
│   ├── providers/              # Telephony provider abstraction
│   │   ├── call_provider.py    # CallSessionProvider & SimulatedCallProvider
│   │   └── __init__.py
│   ├── triage/                 # Hybrid AI Triage Engine (M1..M7)
│   │   ├── normalize.py        # M1: Normalizer & variant folding
│   │   ├── extract.py          # M2: Fact & threat extractor
│   │   ├── geo.py              # Gazetteer & spatial preposition extractor
│   │   ├── covert_detector.py  # M3: Covert & code-word detector
│   │   ├── urgency.py          # M4: Safety-first urgency engine & rules floor
│   │   ├── routing.py          # M5: Multi-label service router
│   │   ├── evidence.py         # M7: Explainer & evidence span highlighter
│   │   └── pipeline.py         # Pipeline orchestrator
│   ├── repeat_matching/        # M6: Cautious repeat matcher
│   │   ├── hashing.py          # HMAC-SHA256 phone hashing
│   │   ├── phonetic.py         # Hinglish phonetic keys
│   │   └── matcher.py          # 2-strong-signals matcher & reversible links
│   ├── dispatch/               # Simulated dispatch engine
│   │   ├── distance.py         # Haversine & route distance calculators
│   │   ├── eta.py              # Dynamic ETA estimator
│   │   ├── assignment.py       # Unit assigner
│   │   └── simulation.py       # State machine stepper
│   ├── services/               # High-level domain services
│   │   ├── incident_service.py # Incident management & live queue
│   │   ├── location_service.py # Location recovery & candidate search
│   │   ├── lexicon_service.py  # Versioned code phrase curator
│   │   └── impact_service.py   # UN SDG metrics aggregator
│   ├── evaluation/             # Evaluation harness
│   │   ├── metrics.py          # Bootstrap CI, under-triage, macro-F1
│   │   └── harness.py          # Benchmark runner & hidden set protocol
│   └── ui/                     # UI components & design system
│       ├── theme.py            # eSahaay CSS design palette & typography
│       ├── components.py       # Headers, chips, and Triage Card
│       └── help_content.py     # Protocols & keyboard shortcuts
├── config/                     # Versioned policy and lexicon configurations
│   ├── policy.yaml             # Thresholds & cost matrices
│   ├── app.yaml                # Application settings
│   └── lexicon/                # Code words and variant dictionaries
├── docs/                       # Architecture, telephony, and safety documentation
│   ├── architecture.md         # System architecture & 10-second path
│   ├── telephony_architecture.md # Exotel Indian telephony recommendation
│   └── safety_design.md        # Safety floor & asymmetry principles
├── scripts/
│   └── seed_demo.py            # Fictional demo dataset seeder & reset tool
└── tests/                      # Automated test suite (37 pytest unit tests)
```

---

## 📜 Disclaimer & Ethical Safeguards

- **Privacy by Design:** Raw phone numbers are never stored in plain text. Keyed HMAC-SHA256 hashes are used for repeat candidate comparisons, and phone numbers are masked in all operator views.
- **Human-in-the-Loop:** eSahaay is a co-pilot that recommends urgency and service routing; a human operator confirms every dispatch. Every priority override is recorded in an immutable audit trail with actor ID, timestamp, and mandatory justification.
- **Hackathon Demonstration Only:** This application is built as a prototype for Hack@BVP 8.0 Problem Statement 3. It is not connected to India's Emergency Response Support System (ERSS / 112) or official police/ambulance infrastructure.
