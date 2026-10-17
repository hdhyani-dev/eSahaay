"""Contextual help content, emergency protocols, and user guides."""

LIVE_CALL_GUIDE = """
### 📞 How to Handle a Live Helpline Call in Ten Seconds

1. **First 3 Seconds — Immediate One-Glance Read:**
   - Check the **Urgency Chip** at the top right:
     - 🚨 **P0 Critical:** Active violence, weapons, breathing difficulty, or unconsciousness.
     - ⚠️ **P1 High:** Threats, active stalking, or covert distress calls.
     - ℹ️ **P2 Medium:** Past incidents, non-urgent harassment, or shelter requests.
     - 📋 **P3 Low:** Informational queries or legal procedure questions.
   - Look at the **VERIFY Banner**: If present, uncertainty or missing location has automatically escalated the urgency.

2. **Next 4 Seconds — Inspect Evidence & Location:**
   - Review highlighted spans in the transcript. Hover to verify which safety rule or model triggered the decision.
   - Verify extracted location. If missing, ask the prompted landmark question.

3. **Final 3 Seconds — Confirm or Override:**
   - Tap **Confirm & Continue** to approve the recommendation.
   - If you notice facts the model missed, tap **Override Priority**, record a brief reason, and proceed.
   - Tap **Proceed to Dispatch** to route response units immediately.
"""

EMERGENCY_PROTOCOLS = """
### 🛡️ Emergency Handling Protocols

#### 1. Covert Distress Calls (Wrong Number / Food Orders)
- **Signal:** Caller asks for "Pizza", "Doctor", "Doodh", or claims "Wrong number" in a whisper or hushed voice.
- **Protocol:**
  - **NEVER** ask open-ended questions.
  - Ask **Yes / No questions ONLY**: *"Are you in danger right now? Say Yes or No."*
  - **DO NOT CALL BACK** to this number if disconnected.
  - Route silently to **Police (112)** and **Shelter / NGO (181)**.

#### 2. Active Domestic Violence
- Route immediately to **Police (112)**. If bleeding or injury is reported, dispatch **Medical (108)** simultaneously.
- If children are crying or present, urgency is locked to **P0 Critical**.

#### 3. Medical Cardiac / Respiratory Emergency
- Route to **Medical / 108 Ambulance** with highest priority.
- If caller is in transit, ask for nearest landmark or metro station gate number.
"""

KEYBOARD_SHORTCUTS = """
### ⌨️ Helpline Operator Keyboard Shortcuts

| Shortcut | Action | Description |
|---|---|---|
| `Ctrl + Enter` | **Confirm Assessment** | Approves recommended priority and services |
| `Alt + O` | **Override Priority** | Opens priority override dialog |
| `Alt + D` | **Open Dispatch** | Transitions directly to simulated dispatch map |
| `Alt + Q` | **Next Queue Call** | Loads next waiting call in the queue |
| `Esc` | **Cancel / Close Modal** | Closes any open dialog or modal |
"""
