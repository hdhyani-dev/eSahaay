# Safety-First Design & Hybrid AI Triage Principles
## eSahaay Emergency Response & Triage System

### 1. Safety Asymmetry Principle
In emergency helpline triage, false negatives (missing or under-triaging a life-threatening crisis) incur an intolerable humanitarian cost, whereas false positives (over-triaging to P0/P1) represent an acceptable price for human safety.

eSahaay embodies this through three non-negotiable architectural guarantees:
1. **Never Silently Downgrade:** If deterministic safety rules fire on credible danger cues (weapons, active assault, cardiac collapse, breathlessness, child at risk), no AI classifier or statistical model may downgrade the case.
2. **Escalation on Uncertainty:** If confidence is below threshold $\tau$ (0.75), or location is unconfirmed on $\ge P1$, or the call is unusually short with danger cues, the system automatically raises the urgency by one level and raises the `VERIFY` flag.
3. **Max-Risk Fusion:** When combining the deterministic Rules Floor ($F_{\text{rules}}$), Covert Signal Floor ($F_{\text{covert}}$), and Model Prediction ($M$), the resulting level is strictly:
   $$\text{Level} = \max(\text{Risk}(F_{\text{rules}}), \text{Risk}(F_{\text{covert}}), \text{Risk}(M))$$

---

### 2. Priority Ladder Definitions

| Level | Descriptor | Operational Meaning | Target Action |
|---|---|---|---|
| **P0** | **Critical** | Immediate or potentially life-threatening danger; active physical violence, weapon, severe trauma, unconsciousness, cardiac arrest. | Immediate dispatch, pinned to top of live queue with pulsating visual alert, alert supervisor. |
| **P1** | **High** | Serious threat or urgent assistance required within hours; stalking escalation, covert code words, trafficking, domestic harassment with escalating threat. | Priority queue; dispatch upon operator confirmation; prompt safe yes/no questions. |
| **P2** | **Medium** | Significant concern requiring timely follow-up; past incident, non-violent harassment complaint, shelter request. | Standard queue; service routing and scheduled dispatch. |
| **P3** | **Low** | Non-immediate informational or legal aid query with zero danger cues. | Provide legal aid contact / guidance; log case. |

---

### 3. Covert Distress & Code Word Detection

Callers under surveillance or domestic coercion cannot always speak openly. They frequently use indirect framings:
- **Food Delivery Code:** Framing the emergency helpline as a pizza order (*"hello... wrong number... aap pizza wali ho?"*).
- **Medical / Doctor Inquiry:** Inquiring about medicine or a doctor in a whisper while barred from leaving.
- **Wrong Number Pretext:** Starting with *"sorry wrong number"* followed by whispers (*"wo mera bhai yahin room ke bahar hai"*).

#### Safe Operator Handling:
1. **Safety Floor Elevation:** Sets urgency to at least **P1** and raises the `COVERT_SIGNAL` flag.
2. **Safe Contact Flag Forced to FALSE:** The system sets `safe_contact_flag = False`. In the UI and all dispatch hand-offs, an explicit warning is displayed: **"DO NOT CALL BACK — Caller is under observation."**
3. **Safe Yes/No Question Suggestion:** Instead of asking open-ended questions that force the caller to speak, the system suggests questions requiring only a monosyllabic yes/no answer:
   - *"Are you in immediate danger right now? Say yes or no."*
   - *"Do you want police dispatched to your location? Say yes or no."*

---

### 4. Cautious Repeat-Complaint Matching: The "2-Strong-Signals" Rule

Merging cases erroneously can corrupt case histories and falsely attribute domestic incidents to innocent third parties. To prevent false merges:
- **Blocking Keys:** Candidates are pre-filtered using three fast blocking keys:
  1. Keyed HMAC-SHA256 phone hash
  2. Phonetic name representation (Metaphone / Hinglish variant mapping)
  3. Locality / place token match
- **Signal Weighting & Scoring:**
  - Phone match: weight 0.45 (strong)
  - Phonetic name similarity: weight 0.20 (medium)
  - Locality match: weight 0.15 (medium)
  - Threat type match: weight 0.10
  - Temporal decay: weight 0.10 (30-day exponential half-life)
- **Three-Band Decision Structure:**
  - **Auto-link:** Score $\ge 0.92$ **AND** at least **two independent strong signals**.
  - **Suggest-only:** Score between $0.55$ and $0.92$.
  - **New Case:** Score $< 0.55$.
- **Reversibility Guarantee:** A link is never a destructive database merge. It is stored as an auditable relationship (`RepeatLink`) that can be unlinked with one click and mandatory audit justification.
