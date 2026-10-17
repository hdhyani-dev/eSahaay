# Sahaay System Architecture & Engineering Specifications

## 1. System Overview & The Ten-Second Path

Sahaay is designed to provide an operator with a complete, safety-first **Triage Card** within a 10-second decision budget when receiving noisy, mixed-language (Hindi, English, Hinglish) emergency helpline calls.

```
+-----------------------------------------------------------------------------------------------------+
|                                 1. INPUT CHANNELS (Text / Stream)                                   |
|   Simulated Inbound Call   │   Batch Test JSONL (Evaluation)   │   Operator Quick Notes / SMS      |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
|                                 2. NLP CORE (M1..M7 Pipeline)                                       |
|  [0 - 1 s]  M1: Normalizer  --> Script ID, Hinglish Transliteration, Phonetic Variant Folding       |
|  [1 - 4 s]  M2: Extractor   --> Facts (Victim, Perp, Injury, Weapon, Ongoing) & Location Candidates |
|             M3: Covert Det  --> Code words, Whispered Speech, Wrong-Number Pretext Detection        |
|             AI Classifier   --> Multilingual Calibrated Confidence Estimator                        |
|  [4 - 5 s]  M4: Urgency Eng --> Safety Rules Floor + Max-Risk Fusion + Uncertainty Escalation      |
|  [5 - 7 s]  M5: Router      --> Multi-label Services (Police, Medical, Shelter, Legal, Counselling) |
|             M6: Matcher     --> Blocking Keys + 2-Strong-Signals Cautious Repeat Linker             |
|  [7 - 10 s] M7: Explainer   --> Highlighting Evidence Spans in Caller's Own Words                  |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
|                              3. EXPERIENCE LAYER (Streamlit Workstation)                            |
|  - Operator Softphone Interface (Ringing alert, Live timer, streaming partial & final text)         |
|  - One-Glance Triage Card (Urgency chip, Confidence bar, Threat, Location, Safe Question prompt)    |
|  - Location Recovery Console (Candidate confirmation, gazetteer search, clarification prompts)      |
|  - Simulated Dispatch State Machine (Available -> Assigned -> Dispatched -> Arrived -> Completed)   |
|  - Cautious Repeat Review (Side-by-side comparison, signal breakdown, one-click undo)              |
|  - Safety Evaluation Dashboard & Hidden-Set Submission Harness                                      |
+-----------------------------------------------------------------------------------------------------+
                                                   │
                                                   ▼
+-----------------------------------------------------------------------------------------------------+
|                              4. PERSISTENT DATA LAYER (SQLAlchemy + SQLite)                         |
|  - Incidents & Cases Table (Urgency, Threat, Location, Safe Contact Flag, Resolution)               |
|  - Transcript Segments (Offsets, Speaker, Raw Text, Normalized Text, Lang Mix, ASR Confidence)      |
|  - Triage Assessments (Confidence, Rules Floor, Model Level, Flags, Routes, Evidence Spans)         |
|  - Response Units & Dispatch Assignments (Coordinates, Haversine Distances, ETAs, Status Lifecycles)|
|  - Reversible Repeat Links (Signals, Confidence, Undo Audit)                                        |
|  - Lexicon Store (Versioned code words and dialect mappings)                                        |
|  - Append-Only Audit Trail (Actors, Roles, Actions, Before/After States, Timestamps)                |
+-----------------------------------------------------------------------------------------------------+
```

---

## 2. Core NLP Modules (M1 — M7)

| Module | Responsibility | Key Input -> Output | Technique |
|---|---|---|---|
| **M1 Normalizer** (`sahaay/triage/normalize.py`) | Make noisy Hinglish comparable | Raw text -> Tokens with script tag, canonical forms | Unicode normalization, Roman-to-Devanagari mapping, edit-distance folding (`maar`/`mar`/`maara`), filler cleanup. |
| **M2 Extractor** (`sahaay/triage/extract.py` & `geo.py`) | Extract structured entities & locations | Tokens -> Location candidates, threat types, facts | Delhi NCR gazetteer, spatial preposition parsing (`ke paas`, `gali no`, `sector`), fact regex & fuzzy matching. |
| **M3 Covert Detector** (`sahaay/triage/covert_detector.py`) | Identify indirect danger & code words | Text + metadata -> Covert level, safe contact flag | Versioned lexicon of food orders, doctor inquires, wrong numbers, whisper markers, evasive brevity check. |
| **M4 Urgency Engine** (`sahaay/triage/urgency.py`) | Decide urgency with safety-first floor | M1-M3 outputs -> Level (P0-P3), confidence, flags | Max-risk fusion, rules floor (`P0` for weapons/violence/cardiac), uncertainty escalation (`VERIFY`). |
| **M5 Service Router** (`sahaay/triage/routing.py`) | Route multi-label emergency services | Threat, urgency, details -> Ordered services list | Policy matrix, time-criticality ordering (Medical before Police for critical injuries). |
| **M6 Repeat Matcher** (`sahaay/repeat_matching/matcher.py`) | Detect repeated complaints safely | New case -> Repeat candidates with bands | Blocking keys (phone hash, phonetic name, locality), 2-strong-signals rule, exponential time decay. |
| **M7 Explainer** (`sahaay/triage/evidence.py`) | Justify decisions transparently | All outputs -> Highlighted evidence spans | Rule attribution, exact character span mapping in caller's own words. |

---

## 3. UN Sustainable Development Goals (SDG) Alignment

- **SDG 5 (Gender Equality):** Rapid detection of domestic violence, stalking, and trafficking, even when spoken in whispers or code phrases. Prompts safe yes/no questions and routes to shelter and legal aid.
- **SDG 16 (Peace, Justice & Strong Institutions):** Faster, auditable emergency response; immutable audit logging; cautious repeat-complaint linking ensures institutional accountability without false profiling.
- **SDG 10 (Reduced Inequalities):** Hinglish, Hindi in Devanagari, romanized Hindi, and dialect phrasing are treated as first-class citizens, ensuring citizens who do not speak English are never underserved.
- **SDG 9 (Industry, Innovation & Infrastructure):** Lightweight, modular architecture runnable locally on CPU with zero mandatory external dependencies, easily deployable as a co-pilot across public helpline infrastructure.
