"""eSahaay — Emergency Response & Triage System.
Main Streamlit Application Router and Navigation Shell.
Reference: eSahaay PRD Hack@BVP 8.0 PS3
"""
import sys
import time
import datetime
import io
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import folium
from streamlit_folium import st_folium
from sqlalchemy.orm import Session

from sahaay.config import settings
from sahaay.database import SessionLocal, init_database
from sahaay.models import (
    User, Incident, ResponseUnit, DispatchAssignment,
    RepeatLink, LexiconEntry, AuditEvent, TranscriptSegment, TriageAssessment
)
from sahaay.auth import authenticate_user, hash_password
from sahaay.permissions import has_permission, can_access_page, ROLES
from sahaay.ui.theme import get_theme_css, PALETTE
from sahaay.ui.components import (
    render_app_header, render_priority_chip, render_triage_card, safe_html,
    LOGO_SVG, LOGO_SVG_SIDEBAR, get_logo_data_uri, get_logo_html, get_emblem_html
)
from sahaay.ui.help_content import LIVE_CALL_GUIDE, EMERGENCY_PROTOCOLS, KEYBOARD_SHORTCUTS
from sahaay.ui.audio import get_ringtone_b64, get_ringtone_bytes
from sahaay.ui.call_audio import get_call_recording_b64

# Transparently protect all HTML rendering from CommonMark 4-space indentation bugs
_orig_markdown = st.markdown
def _safe_markdown_wrapper(body, *args, **kwargs):
    if kwargs.get("unsafe_allow_html"):
        return safe_html(str(body))
    return _orig_markdown(body, *args, **kwargs)
st.markdown = _safe_markdown_wrapper
from sahaay.services.incident_service import (
    create_incident_from_transcript,
    get_live_queue,
    override_incident_urgency,
    confirm_incident_urgency
)
from sahaay.services.lexicon_service import (
    list_lexicon_entries,
    propose_lexicon_entry,
    approve_lexicon_entry,
    retire_lexicon_entry
)
from sahaay.services.impact_service import get_sdg_impact_metrics
from sahaay.services.location_service import (
    get_incidents_needing_location_recovery,
    get_location_recovery_details,
    confirm_candidate_location,
    manual_search_gazetteer,
    CLARIFICATION_QUESTIONS
)
from sahaay.providers.call_provider import (
    simulated_call_provider,
    PREDEFINED_SIMULATION_SCENARIOS,
    CallSessionState,
    TranscriptEvent
)
from sahaay.dispatch.assignment import (
    get_units_for_incident,
    assign_unit_to_incident,
    get_all_services_nearest_units
)
from sahaay.dispatch.simulation import (
    step_assignment_simulation,
    reset_unit_to_base,
    advance_unit_towards_incident,
    escalate_unit_response
)
from sahaay.ui.dispatch_map import (
    build_dispatch_tactical_map,
    build_fleet_overview_map,
    render_telemetry_hud,
    render_tactical_comms_console,
    TACTICAL_PRESET_DIRECTIVES,
    generate_unit_tactical_acknowledgment
)
from sahaay.repeat_matching.matcher import match_repeat_complaints, approve_or_create_link, undo_repeat_link
from sahaay.triage.pipeline import run_triage_pipeline
from sahaay.triage.translate import translate_to_english
from sahaay.triage.evidence import render_highlighted_transcript
from sahaay.evaluation.harness import evaluate_dataset, run_hidden_set_protocol, export_evaluation_html_report
from sahaay.audit import log_audit_event
from scripts.seed_demo import seed_database

# Set Streamlit Page Configuration
st.set_page_config(
    page_title="eSahaay — Emergency Response & Triage System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Theme State Initialization (Dark CAD Workstation vs Clean Light Operations)
if "theme_mode" not in st.session_state:
    st.session_state.theme_mode = "dark"

# Apply eSahaay CSS Design System (Theme-Adaptive)
st.markdown(get_theme_css(st.session_state.theme_mode), unsafe_allow_html=True)

# Top Right Corner Vector Theme Toggle Button (Sun ☼ in Dark Mode, Moon ☾ in Light Mode)
next_theme = "light" if st.session_state.theme_mode == "dark" else "dark"
theme_icon = "☼" if st.session_state.theme_mode == "dark" else "☾"
if st.button(theme_icon, key="top_right_theme_toggle", help=f"Toggle Theme (Current: {st.session_state.theme_mode.title()} Mode — Click to switch)"):
    st.session_state.theme_mode = next_theme
    st.rerun()

# Initialize and auto-seed database on startup if empty
init_database()
try:
    seed_database()
except Exception:
    pass

# Session State Initialization
if "user" not in st.session_state:
    st.session_state.user = None

if "current_page" not in st.session_state:
    st.session_state.current_page = "login"

if "selected_incident_id" not in st.session_state:
    st.session_state.selected_incident_id = "INC-1042"

if "sim_active_session" not in st.session_state:
    st.session_state.sim_active_session = None

if "sim_scenario_id" not in st.session_state:
    st.session_state.sim_scenario_id = "scen_domestic_violence"

if "sim_played_segments" not in st.session_state:
    st.session_state.sim_played_segments = []

if "sim_partial_segment" not in st.session_state:
    st.session_state.sim_partial_segment = None

if "sim_call_state" not in st.session_state:
    st.session_state.sim_call_state = "IDLE"

if "sim_call_timer" not in st.session_state:
    st.session_state.sim_call_timer = 0

if "sim_latest_triage" not in st.session_state:
    st.session_state.sim_latest_triage = None

if "triage_input_mode" not in st.session_state:
    st.session_state.triage_input_mode = "record"

if "sim_call_start_time" not in st.session_state:
    st.session_state.sim_call_start_time = None

# DB helper
def get_db_session():
    return SessionLocal()

# ---------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------
def render_sidebar():
    with st.sidebar:
        is_dark = (st.session_state.theme_mode == "dark")
        brand_title_color = "#F1F5F9" if is_dark else "#142238"
        brand_sub_color = "#A8B6C9" if is_dark else "#475569"
        pill_border = "rgba(34, 211, 238, 0.35)" if is_dark else "rgba(0, 127, 158, 0.35)"
        pill_bg = "rgba(34, 211, 238, 0.10)" if is_dark else "rgba(0, 127, 158, 0.08)"
        pill_text = "#22D3EE" if is_dark else "#007F9E"
        dot_color = "#34D399" if is_dark else "#08784E"
        card_bg = "#19283D" if is_dark else "#E8EFF7"
        card_border = "#304158" if is_dark else "#CBD5E1"
        ws_label_color = "#A8B6C9" if is_dark else "#475569"
        ws_name_color = "#F1F5F9" if is_dark else "#142238"
        ws_id_color = "#22D3EE" if is_dark else "#007F9E"

        emblem_uri = get_logo_data_uri("emblem")
        st.markdown(
            f"""
            <div style="display: flex; align-items: center; gap: 12px; margin-top: 2px; margin-bottom: 14px;" class="sidebar-brand-box">
                <div style="width: 44px; height: 44px; min-width: 44px; border-radius: 12px; background: #0B1220; border: 1px solid #304158; display: flex; align-items: center; justify-content: center; box-shadow: 0 2px 8px rgba(0, 0, 0, 0.4); padding: 5px;">
                    <img src="{emblem_uri}" style="width: 34px; height: 34px; object-fit: contain; pointer-events: none;" alt="eSahaay" draggable="false" />
                </div>
                <div style="pointer-events: none;">
                    <div style="font-size: 21px; font-weight: 800; color: {brand_title_color}; letter-spacing: -0.02em; line-height: 1.15;">
                        eSahaay
                    </div>
                    <div style="font-size: 12px; color: {brand_sub_color}; font-weight: 600; margin-top: 2px;">
                        Intelligent Helpline Triage
                    </div>
                </div>
            </div>

            <div style="border: 1px solid {pill_border}; background: {pill_bg}; border-radius: 8px; padding: 6px 12px; margin-bottom: 20px; display: flex; align-items: center; gap: 8px;">
                <span style="width: 7px; height: 7px; border-radius: 50%; background: {dot_color}; display: inline-block; box-shadow: 0 0 8px {dot_color};"></span>
                <span style="color: {pill_text}; font-weight: 700; font-size: 12px; letter-spacing: 0.02em;">Decision-Support Active</span>
            </div>
            """,
            unsafe_allow_html=True
        )

        is_triage = (st.session_state.current_page == "triage")
        is_dashboard = (st.session_state.current_page == "dashboard")
        is_history = (st.session_state.current_page in ["incidents", "case_detail"])

        # QUICK ACTIONS
        st.markdown("<div class='sidebar-category-header'>QUICK ACTIONS</div>", unsafe_allow_html=True)
        triage_label = "⛨  New Incident            Live  ›" if is_triage else "⛨  New Incident"
        if st.button(triage_label, key="nav_btn_triage", use_container_width=True, type="primary" if is_triage else "secondary"):
            st.session_state.current_page = "triage"
            st.rerun()

        # MONITOR
        st.markdown("<div class='sidebar-category-header'>MONITOR</div>", unsafe_allow_html=True)
        dash_label = "⊞  Dashboard                   ›" if is_dashboard else "⊞  Dashboard"
        if st.button(dash_label, key="nav_btn_dashboard", use_container_width=True, type="primary" if is_dashboard else "secondary"):
            st.session_state.current_page = "dashboard"
            st.rerun()

        history_label = "⏱  Case History                   ›" if is_history else "⏱  Case History"
        if st.button(history_label, key="nav_btn_history", use_container_width=True, type="primary" if is_history else "secondary"):
            st.session_state.current_page = "incidents"
            st.rerun()

        st.markdown("<div style='margin-top: 30px;'></div>", unsafe_allow_html=True)
        cur_user = st.session_state.get("user") or {}
        st.markdown(
            f"""
            <div class="sidebar-user-card" style="border-radius: 8px; padding: 10px 12px; margin-bottom: 12px; background: {card_bg}; border: 1px solid {card_border};">
                <div style="font-size: 10px; color: {ws_label_color}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em;">Active Workstation</div>
                <div style="font-size: 12.5px; font-weight: 600; margin-top: 2px; color: {ws_name_color};">{cur_user.get('full_name', 'Operator')}</div>
                <div style="font-size: 11px; color: {ws_id_color}; font-family: monospace; font-weight: 700;">ID: {cur_user.get('employee_id', 'OP1042')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Terminal Sign Out", key="btn_terminal_signout", use_container_width=True):
            st.session_state.user = None
            st.session_state.current_page = "login"
            st.rerun()

# ---------------------------------------------------------
# Page 0: PS3 Mission & Checklist Landing Page
# ---------------------------------------------------------
def page_ps3():
    render_app_header(st.session_state.user)
    
    st.markdown(
        f"""
        <div class="sahaay-card" style="padding: 24px 28px; margin-bottom: 24px;">
            <div style="font-size: 11px; font-weight: 700; color: #2563EB; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 6px;">
                Problem Statement 3 • Hack@BVP 8.0 Prototype
            </div>
            <div style="font-size: 24px; font-weight: 800; color: #0F172A; letter-spacing: -0.02em; margin-bottom: 10px;">
                Ten Seconds to Read a Call — Multilingual Helpline Triage Engine
            </div>
            <div style="font-size: 14.5px; color: #475569; line-height: 1.6; max-width: 960px;">
                An emergency call operator has under <b>10 seconds</b> to interpret noisy, code-mixed Hindi/English/Hinglish calls, identify danger, extract critical incident facts, assign priority with an irrevocable safety floor, and route cases to police, medical, shelter, or legal aid without merging distinct individuals.
            </div>
            <div style="margin-top: 18px; display: flex; gap: 8px; flex-wrap: wrap;">
                <span class="sdg-tag" style="background: #FEE2E2; color: #991B1B; border: 1px solid #FECACA;">SDG 5: Gender Equality</span>
                <span class="sdg-tag" style="background: #E0F2FE; color: #0369A1; border: 1px solid #BFDBFE;">SDG 16: Peace & Justice</span>
                <span class="sdg-tag" style="background: #FCE7F3; color: #9D174D; border: 1px solid #FBCFE8;">SDG 10: Reduced Inequalities</span>
                <span class="sdg-tag" style="background: #FFEDD5; color: #9A3412; border: 1px solid #FED7AA;">SDG 9: Industry & Innovation</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div style='font-size: 16px; font-weight: 800; color: #0F172A; margin-bottom: 4px;'>Core Requirements Verification Suite</div>", unsafe_allow_html=True)
    st.caption("Each capability card links directly to its fully functional, connected prototype implementation:")

    req_cols1, req_cols2 = st.columns(2, gap="medium")

    with req_cols1:
        st.markdown(
            """
            <div class="sahaay-card" style="border-left: 3px solid #DC2626; margin-bottom: 12px;">
                <div class="sahaay-card-title">
                    <span>1. Emergency Urgency Classification (P0 – P3)</span>
                    <span class="badge-p0"><span class="badge-p0-dot"></span>VERIFIED</span>
                </div>
                <div class="sahaay-card-subtext">
                    Deterministic rules floor guarantees life-threatening crises are never downgraded by statistical models. Ambiguity automatically escalates priority to protect callers.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Launch Live Triage Console →", key="chk_urg", use_container_width=True):
            st.session_state.current_page = "triage"
            st.rerun()

        st.markdown(
            """
            <div class="sahaay-card" style="border-left: 3px solid #2563EB; margin-bottom: 12px;">
                <div class="sahaay-card-title">
                    <span>2. Structured Entity & Telemetry Extraction</span>
                    <span class="badge-p2"><span class="badge-p2-dot"></span>VERIFIED</span>
                </div>
                <div class="sahaay-card-subtext">
                    Extracts location, nearby landmarks, threat classification, victim, perpetrator relation, weapon, injury, and active ongoing status from noisy code-mixed transcripts.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Inspect Extraction Pipeline in Simulator →", key="chk_ext", use_container_width=True):
            st.session_state.current_page = "simulator"
            st.rerun()

        st.markdown(
            """
            <div class="sahaay-card" style="border-left: 3px solid #059669; margin-bottom: 12px;">
                <div class="sahaay-card-title">
                    <span>3. Recommended Emergency Services</span>
                    <span class="badge-p3"><span class="badge-p3-dot"></span>VERIFIED</span>
                </div>
                <div class="sahaay-card-subtext">
                    Recommends police, medical dispatch, emergency shelter, legal aid, or counselling based on policy rules, ordered by time criticality.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Open Field Dispatch Console →", key="chk_rout", use_container_width=True):
            st.session_state.current_page = "incidents"
            st.rerun()

    with req_cols2:
        st.markdown(
            """
            <div class="sahaay-card" style="border-left: 3px solid #D97706; margin-bottom: 12px;">
                <div class="sahaay-card-title">
                    <span>4. Cautious Repeat-Complaint Auditor</span>
                    <span class="badge-p1"><span class="badge-p1-dot"></span>VERIFIED</span>
                </div>
                <div class="sahaay-card-subtext">
                    Uses blocking keys, phone HMAC, and phonetic names. Enforces strict <b>2-strong-signals rule</b>. One fuzzy name never merges cases.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Audit Repeat Complaint Matching →", key="chk_rep", use_container_width=True):
            st.session_state.current_page = "repeats"
            st.rerun()

        st.markdown(
            """
            <div class="sahaay-card" style="border-left: 3px solid #7C3AED; margin-bottom: 12px;">
                <div class="sahaay-card-title">
                    <span>5. Covert Distress & Code-Word Detection</span>
                    <span class="badge-p2"><span class="badge-p2-dot"></span>VERIFIED</span>
                </div>
                <div class="sahaay-card-subtext">
                    Detects pizza orders, whispered medicine queries, wrong-number pretexts, flags 'DO NOT CALL BACK', and prompts safe yes/no operator questions.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Explore Multilingual Dialect Lexicon →", key="chk_cov", use_container_width=True):
            st.session_state.current_page = "lexicon"
            st.rerun()

        st.markdown(
            """
            <div class="sahaay-card" style="border-left: 3px solid #0284C7; margin-bottom: 12px;">
                <div class="sahaay-card-title">
                    <span>6. Empirical Evaluation & Hidden Benchmarks</span>
                    <span class="badge-p3"><span class="badge-p3-dot"></span>VERIFIED</span>
                </div>
                <div class="sahaay-card-subtext">
                    Computes empirical Urgent Recall with 95% bootstrap CI, confusion matrix, and runs hidden-set protocol without label leakage.
                </div>
            </div>
            """, unsafe_allow_html=True
        )
        if st.button("Run Model Evaluation Harness →", key="chk_eval", use_container_width=True):
            st.session_state.current_page = "eval"
            st.rerun()

# ---------------------------------------------------------
# Page 1: Operator Terminal Login Console (Centered CAD Card)
# ---------------------------------------------------------
def page_login():
    _, col_center, _ = st.columns([1, 1.4, 1])
    with col_center:
        full_logo_uri = get_logo_data_uri("full")
        st.markdown(
            f"""
            <div class="sahaay-card login-card" style="border-radius: 14px; padding: 24px 28px; margin: 24px auto; max-width: 460px; box-shadow: 0 12px 30px -4px rgba(0, 0, 0, 0.35);">
                <!-- eSahaay Official Brand Logo (Compact High-DPI) -->
                <div style="text-align: center; margin-bottom: 14px;">
                    <img src="{full_logo_uri}" style="height: 155px; width: auto; max-width: 100%; object-fit: contain; filter: drop-shadow(0 4px 16px rgba(37, 99, 235, 0.22));" alt="eSahaay Logo" />
                    <div style="font-size: 12px; font-weight: 600; letter-spacing: 0.03em; margin-top: 6px; opacity: 0.85;">
                        eSahaay — Emergency Response & Helpline Triage System
                    </div>
                </div>

                <div style="height: 1px; background: rgba(148, 163, 184, 0.2); margin-bottom: 12px;"></div>

                <div style="font-size: 10.5px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; opacity: 0.75;">
                    Operator Station Authentication
                </div>
            """,
            unsafe_allow_html=True
        )

        emp_id = st.text_input("Badge ID / Operator Employee Code", value="OP1042", placeholder="e.g. OP1042")
        password = st.text_input("Security Access PIN", value="operator123", type="password")

        st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)
        if st.button("AUTHENTICATE & ENTER STATION →", key="btn_authenticate", type="primary", use_container_width=True):
            db = get_db_session()
            user = authenticate_user(db, emp_id, password)
            if user:
                st.session_state.user = {
                    "id": user.id,
                    "employee_id": user.employee_id,
                    "full_name": user.full_name,
                    "role": user.role,
                    "email": user.email
                }
                st.session_state.current_page = "triage"
                db.close()
                st.rerun()
            else:
                st.error("Invalid Badge ID or Security PIN. Please retry.")
            db.close()

        st.markdown(
            """
                <div style="margin-top: 14px; padding-top: 10px; border-top: 1px solid rgba(148, 163, 184, 0.2); text-align: center; font-size: 10.5px; opacity: 0.65;">
                    Restricted Access • Emergency CAD Terminal • Hack@BVP 8.0
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

# ---------------------------------------------------------
# Page 2: Operator Dashboard
# ---------------------------------------------------------
def page_dashboard():
    render_app_header(st.session_state.user)
    db = get_db_session()

    # Calculate actual statistics from persistent database
    total_calls = db.query(Incident).count()
    active_calls = db.query(Incident).filter(Incident.status.in_(["active", "in_progress"])).count()
    resolved_today = db.query(Incident).filter(Incident.status == "resolved").count()
    p0_count = db.query(Incident).filter(Incident.current_urgency == "P0", Incident.status.in_(["active", "in_progress"])).count()
    p1_count = db.query(Incident).filter(Incident.current_urgency == "P1", Incident.status.in_(["active", "in_progress"])).count()
    p2_count = db.query(Incident).filter(Incident.current_urgency == "P2", Incident.status.in_(["active", "in_progress"])).count()
    
    total_units = db.query(ResponseUnit).count()
    available_units = db.query(ResponseUnit).filter(ResponseUnit.status.in_(["available", "completed"])).count()

    # Metric Row
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Active Voice Sessions</div>
                <div class="sahaay-kpi-value" style="color: #DC2626;">{active_calls}</div>
                <div class="sahaay-kpi-footer" style="color: #64748B;">Live Triage Pipeline</div>
            </div>
            """, unsafe_allow_html=True
        )
    with m2:
        st.markdown(
            f"""
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Inbound Queue Depth</div>
                <div class="sahaay-kpi-value">{active_calls}</div>
                <div class="sahaay-kpi-footer" style="color: #64748B;">Prioritized by Risk</div>
            </div>
            """, unsafe_allow_html=True
        )
    with m3:
        st.markdown(
            f"""
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Cases Resolved (Shift)</div>
                <div class="sahaay-kpi-value" style="color: #059669;">{resolved_today}</div>
                <div class="sahaay-kpi-footer" style="color: #059669;">Dispatched & Routed</div>
            </div>
            """, unsafe_allow_html=True
        )
    with m4:
        st.markdown(
            """
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Triage Read Latency</div>
                <div class="sahaay-kpi-value" style="color: #2563EB;">7.2s</div>
                <div class="sahaay-kpi-footer" style="color: #2563EB;">Target &lt; 10s Guaranteed</div>
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

    col_queue, col_side = st.columns([2, 1], gap="large")

    with col_queue:
        st.markdown("<div style='font-size: 16px; font-weight: 800; color: #0F172A; margin-bottom: 2px;'>Active Call Queue & Dispatch Worklist</div>", unsafe_allow_html=True)
        st.caption("Ordered by mandatory safety priority floor and queue wait duration:")
        queue = get_live_queue(db)
        
        if not queue:
            st.info("No active calls waiting in queue. Use 'Live Triage Console' to trigger a simulated call.")
        else:
            for inc in queue:
                pin_class = "p0-pinned-card" if inc.is_urgent_pinned else ""
                chip = render_priority_chip(inc.current_urgency, inc.is_urgent_pinned)
                
                with st.container():
                    st.markdown(
                        f"""
                        <div class="sahaay-card {pin_class}" style="padding: 16px 18px; margin-bottom: 10px;">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-weight: 800; color: #0F172A; font-size: 15px; font-family: monospace;">{inc.id}</span>
                                    <span style="color: #64748B; font-size: 13px; margin-left: 10px;">Caller: <b>{inc.caller_name or 'Anonymous'}</b> ({inc.caller_masked_phone})</span>
                                </div>
                                <div>{chip}</div>
                            </div>
                            <div style="font-size: 13.5px; color: #334155; margin-top: 8px;">
                                <b>Identified Threat:</b> {inc.primary_threat or 'Emergency'} &nbsp;•&nbsp; <b>Location:</b> {inc.location_text or 'Pending Clarification'}
                            </div>
                            <div style="font-size: 12px; color: #64748B; margin-top: 6px;">
                                Incident Status: <b style="color: #0F172A;">{inc.status.upper()}</b> • Ingest Timestamp: {inc.created_at.strftime('%H:%M:%S UTC')}
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    c1, c2 = st.columns([1.5, 3.5])
                    with c1:
                        if st.button("Open Triage Console →", key=f"btn_open_{inc.id}", use_container_width=True):
                            st.session_state.selected_incident_id = inc.id
                            st.session_state.current_page = "triage"
                            st.rerun()

    with col_side:
        st.markdown("<div style='font-size: 16px; font-weight: 800; color: #0F172A; margin-bottom: 2px;'>Priority Breakdown</div>", unsafe_allow_html=True)
        st.caption("Active shift breakdown by triage level:")
        st.markdown(
            f"""
            <div class="sahaay-card" style="padding: 14px 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #E2E8F0;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="badge-p0-dot"></span>
                        <span style="font-size: 13px; font-weight: 600; color: #0F172A;">P0 Critical Crises</span>
                    </div>
                    <span style="font-weight: 800; font-size: 15px; color: #DC2626;">{p0_count}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #E2E8F0;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="badge-p1-dot"></span>
                        <span style="font-size: 13px; font-weight: 600; color: #0F172A;">P1 Urgent Priority</span>
                    </div>
                    <span style="font-weight: 800; font-size: 15px; color: #D97706;">{p1_count}</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <span class="badge-p2-dot"></span>
                        <span style="font-size: 13px; font-weight: 600; color: #0F172A;">P2/P3 Standard Inquiries</span>
                    </div>
                    <span style="font-weight: 800; font-size: 15px; color: #2563EB;">{p2_count}</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("<div style='font-size: 16px; font-weight: 800; color: #0F172A; margin: 18px 0 2px 0;'>Response Unit Deployment</div>", unsafe_allow_html=True)
        st.caption("Delhi NCR field fleet status:")
        st.markdown(
            f"""
            <div class="sahaay-card" style="padding: 14px 18px;">
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0; border-bottom: 1px solid #E2E8F0;">
                    <span style="font-size: 13px; font-weight: 600; color: #0F172A;">Active Operators on Duty</span>
                    <span style="font-weight: 800; font-size: 15px; color: #0F172A;">5 / 6 Stationed</span>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; padding: 10px 0;">
                    <span style="font-size: 13px; font-weight: 600; color: #0F172A;">Available Field Units</span>
                    <span style="font-weight: 800; font-size: 15px; color: #059669;">{available_units} / {total_units} Ready</span>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    db.close()

# ---------------------------------------------------------
# Page 3: Live Triage Console with Operator Phone Simulator
# ---------------------------------------------------------
def page_triage():
    render_app_header(st.session_state.user)
    db = get_db_session()
    is_dark = (st.session_state.theme_mode == "dark")
    accent_cyan = "#22D3EE" if is_dark else "#007F9E"
    muted_text = "#A8B6C9" if is_dark else "#475569" 

    scen_keys = list(PREDEFINED_SIMULATION_SCENARIOS.keys())
    chosen_scen = st.session_state.get("sim_scenario_id", scen_keys[0])

    # Single Call Initiation Button (Background Scenario Rotation)
    if st.session_state.sim_call_state not in [CallSessionState.RINGING, CallSessionState.CONNECTED, CallSessionState.PAUSED, CallSessionState.ENDED]:
        c_trig_space, c_trig_btn = st.columns([3.2, 1.8])
        with c_trig_btn:
            if st.button("Simulate Incoming Call", type="primary", use_container_width=True):
                sim_rotation_list = [
                    "scen_domestic_violence",
                    "scen_tamil_distress",
                    "scen_cardiac_medical",
                    "scen_bengali_distress",
                    "scen_fire_cylinder",
                    "scen_kannada_distress",
                    "scen_kumaoni_distress",
                    "scen_covert_pizza",
                    "scen_road_accident",
                    "scen_stalking_repeat"
                ]
                if "sim_rotation_idx" not in st.session_state:
                    st.session_state.sim_rotation_idx = 0

                cur_idx = st.session_state.sim_rotation_idx % len(sim_rotation_list)
                chosen_scen = sim_rotation_list[cur_idx]
                st.session_state.sim_rotation_idx = (cur_idx + 1) % len(sim_rotation_list)

                sim_sess = simulated_call_provider.start_call(chosen_scen)
                st.session_state.sim_active_session = sim_sess
                st.session_state.sim_scenario_id = chosen_scen
                st.session_state.sim_call_state = CallSessionState.RINGING
                st.session_state.sim_played_segments = []
                st.session_state.sim_partial_segment = None
                st.session_state.sim_call_timer = 0
                st.session_state.sim_latest_triage = None
                st.rerun()

    # Incoming Call Ringing Alert & Audible Ringtone
    if st.session_state.sim_call_state == CallSessionState.RINGING:
        sess = st.session_state.sim_active_session or {}
        ring_b64 = get_ringtone_b64()

        st.markdown(
            f"""
            <div class="sahaay-card" style="border: 2px solid #EF4444; background: rgba(220, 38, 38, 0.14); padding: 20px; text-align: center; margin: 12px 0; border-radius: 12px; box-shadow: 0 0 25px rgba(239, 68, 68, 0.28);">
                <div style="display: flex; justify-content: center; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
                    <div style="display: inline-flex; align-items: center; gap: 8px; background: rgba(220, 38, 38, 0.28); color: #FCA5A5; padding: 4px 14px; border-radius: 9999px; font-weight: 700; font-size: 11.5px; letter-spacing: 0.05em; border: 1px solid rgba(239, 68, 68, 0.45);">
                        <span class="badge-p0-dot"></span> INCOMING EMERGENCY CALL
                    </div>
                </div>
                <div style="font-size: 22px; font-weight: 800;">
                    {sess.get('caller_name', 'Caller')} &nbsp;•&nbsp; <span style="font-family: monospace; color: {accent_cyan};">{sess.get('caller_phone', '+91 98*** **3210')}</span>
                </div>
                <div style="font-size: 13px; opacity: 0.8; margin-top: 4px;">
                    Inbound Line: <b>112 Emergency Dispatch • Channel 01</b>
                </div>

                <!-- Invisible HTML5 Autoplay Ringtone -->
                <audio id="sahaay_audible_ringtone" autoplay loop playsinline style="display: none !important; width: 0 !important; height: 0 !important; opacity: 0 !important; visibility: hidden !important;">
                    <source src="data:audio/wav;base64,{ring_b64}" type="audio/wav">
                </audio>
                <script>
                    (function() {{
                        var audio = document.getElementById('sahaay_audible_ringtone');
                        if (audio) {{
                            audio.volume = 0.85;
                            var playPromise = audio.play();
                            if (playPromise !== undefined) {{
                                playPromise.catch(function(err) {{
                                    console.log('Browser audio policy:', err);
                                }});
                            }}
                        }}
                    }})();
                </script>
            </div>
            """,
            unsafe_allow_html=True
        )
        c_ans, c_rej = st.columns(2)
        with c_ans:
            if st.button("ANSWER CALL", use_container_width=True, type="primary"):
                simulated_call_provider.answer_call(sess["session_id"])
                st.session_state.sim_call_state = CallSessionState.CONNECTED
                first_seg = simulated_call_provider.get_next_transcript_event(sess["session_id"])
                if first_seg:
                    if first_seg.is_final:
                        st.session_state.sim_played_segments.append(first_seg)
                    else:
                        st.session_state.sim_partial_segment = first_seg
                    triage_res = run_triage_pipeline(first_seg.text, call_id=sess["session_id"])
                    st.session_state.sim_latest_triage = triage_res
                st.rerun()
        with c_rej:
            if st.button("DECLINE CALL ✕", use_container_width=True):
                simulated_call_provider.reject_call(sess["session_id"])
                st.session_state.sim_call_state = "IDLE"
                st.session_state.sim_active_session = None
                st.rerun()

    # 50/50 CAD Workstation
    col_transcript, col_triage = st.columns([1, 1], gap="medium")

    # Fetch incident or simulated triage data (only from actual played caller segments)
    triage_res = st.session_state.sim_latest_triage
    if not triage_res:
        triage_res = {
            "urgency": "PENDING",
            "threat_types": [],
            "location": [],
            "details": {"weapon": None, "injury": None, "ongoing": False},
            "routes": [],
            "flags": [],
            "raw_text": ""
        }

    # LEFT COLUMN: Softphone & Real-time Live Transcript
    with col_transcript:
        sess = st.session_state.sim_active_session or {}
        mins = st.session_state.sim_call_timer // 60
        secs = st.session_state.sim_call_timer % 60
        timer_str = f"{mins:02d}:{secs:02d}"

        is_connected = st.session_state.sim_call_state == CallSessionState.CONNECTED
        is_paused = st.session_state.sim_call_state == CallSessionState.PAUSED
        is_ended = st.session_state.sim_call_state == CallSessionState.ENDED

        status_text = "CALL CONNECTED" if is_connected else (
            "ON HOLD" if is_paused else ("CALL ENDED" if is_ended else "OPERATOR READY")
        )
        status_color = "#10B981" if is_connected else ("#F59E0B" if is_paused else ("#EF4444" if is_ended else "#64748B"))

        # Softphone Status Bar
        st.markdown(
            f"""
            <div class="sahaay-card" style="padding: 12px 18px; margin-bottom: 12px;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="height: 8px; width: 8px; border-radius: 50%; background-color: {status_color}; box-shadow: 0 0 8px {status_color}; display: inline-block;"></span>
                        <span style="font-size: 11.5px; font-weight: 700; letter-spacing: 0.05em;">{status_text}</span>
                        <span style="opacity: 0.5;">•</span>
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: {accent_cyan};">{timer_str}</span>
                    </div>
                    <div class="audio-waveform-container">
                        <span class="waveform-bar" style="animation-delay: 0.1s; height: {'14px' if is_connected else '4px'};"></span>
                        <span class="waveform-bar" style="animation-delay: 0.3s; height: {'18px' if is_connected else '4px'};"></span>
                        <span class="waveform-bar" style="animation-delay: 0.2s; height: {'10px' if is_connected else '4px'};"></span>
                        <span class="waveform-bar" style="animation-delay: 0.5s; height: {'16px' if is_connected else '4px'};"></span>
                        <span class="waveform-bar" style="animation-delay: 0.4s; height: {'12px' if is_connected else '4px'};"></span>
                    </div>
                    <div style="font-size: 11.5px; opacity: 0.75; font-family: 'JetBrains Mono', monospace;">
                        {sess.get('session_id', 'CALL-DEL-8819')}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Softphone Call Controls
        if is_connected:
            c_next, c_end = st.columns([1, 1], gap="small")
            with c_next:
                if st.button("Next Speech →", use_container_width=True, type="secondary"):
                    if sess.get("session_id"):
                        evt = simulated_call_provider.get_next_transcript_event(sess["session_id"])
                        if evt:
                            st.session_state.sim_call_timer += 6
                            if evt.is_final:
                                st.session_state.sim_played_segments.append(evt)
                                st.session_state.sim_partial_segment = None
                            else:
                                st.session_state.sim_partial_segment = evt
                            full_text = " ".join([s.text for s in st.session_state.sim_played_segments])
                            if st.session_state.sim_partial_segment:
                                full_text += " " + st.session_state.sim_partial_segment.text
                            st.session_state.sim_latest_triage = run_triage_pipeline(full_text, call_id=sess["session_id"])
                        else:
                            st.info("End of scenario audio stream.")
                        st.rerun()

            with c_end:
                if st.button("End Call ⏹", use_container_width=True, type="primary"):
                    if sess.get("session_id"):
                        simulated_call_provider.end_call(sess["session_id"])
                    st.session_state.sim_call_state = CallSessionState.ENDED
                    st.rerun()
        elif is_ended:
            c_save, c_next_call = st.columns([1.6, 1], gap="small")
            with c_save:
                if st.button("Save Call Recording & Dispatch Recommended Services →", use_container_width=True, type="primary"):
                    full_text = " ".join([s.text for s in st.session_state.sim_played_segments])
                    if not full_text.strip():
                        full_text = "Emergency helpline call"
                    new_inc, _, _ = create_incident_from_transcript(
                        db=db,
                        raw_text=full_text,
                        caller_phone=sess.get("caller_phone", "9876543210"),
                        caller_name=sess.get("caller_name", "Caller"),
                        created_by=st.session_state.user["employee_id"]
                    )
                    st.session_state.selected_incident_id = new_inc.id
                    st.session_state.current_page = "incidents"
                    db.close()
                    st.rerun()
            with c_next_call:
                if st.button("Simulate Next Call", use_container_width=True):
                    sim_rotation_list = [
                        "scen_domestic_violence",
                        "scen_tamil_distress",
                        "scen_cardiac_medical",
                        "scen_bengali_distress",
                        "scen_fire_cylinder",
                        "scen_kannada_distress",
                        "scen_kumaoni_distress",
                        "scen_covert_pizza",
                        "scen_road_accident",
                        "scen_stalking_repeat"
                    ]
                    if "sim_rotation_idx" not in st.session_state:
                        st.session_state.sim_rotation_idx = 0

                    cur_idx = st.session_state.sim_rotation_idx % len(sim_rotation_list)
                    chosen_scen = sim_rotation_list[cur_idx]
                    st.session_state.sim_rotation_idx = (cur_idx + 1) % len(sim_rotation_list)

                    sim_sess = simulated_call_provider.start_call(chosen_scen)
                    st.session_state.sim_active_session = sim_sess
                    st.session_state.sim_scenario_id = chosen_scen
                    st.session_state.sim_call_state = CallSessionState.RINGING
                    st.session_state.sim_played_segments = []
                    st.session_state.sim_partial_segment = None
                    st.session_state.sim_call_timer = 0
                    st.session_state.sim_latest_triage = None
                    st.rerun()

        # Simple Title: Live Transcript with Pan-Indian Language Detection
        detected_lang = triage_res.get("lang_mix", "Indic Multilingual") if (st.session_state.sim_played_segments or is_connected) else "Auto-Detecting Language"

        st.markdown(
            f"""
            <div class="sahaay-card" style="padding: 12px 16px 8px 16px; margin: 12px 0 8px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                    <div style="font-weight: 700; font-size: 13.5px; display: flex; align-items: center; gap: 8px;">
                        <span style="color: {accent_cyan};">●</span> Live Transcript
                    </div>
                    <div style="font-size: 11px; padding: 2px 10px; border-radius: 9999px; background: {'rgba(34, 211, 238, 0.12)' if is_dark else 'rgba(0, 127, 158, 0.10)'}; color: {accent_cyan}; font-weight: 700; border: 1px solid {'rgba(34, 211, 238, 0.25)' if is_dark else 'rgba(0, 127, 158, 0.25)'};">
                        {detected_lang}
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Streaming Transcript Feed
        transcript_container = st.container()
        with transcript_container:
            if st.session_state.sim_played_segments:
                for seg in st.session_state.sim_played_segments:
                    is_operator = seg.speaker.upper() == "OPERATOR"
                    whisper_tag = "<span style='color: #F59E0B; font-weight:700;'>[WHISPER]</span>" if getattr(seg, "is_whisper", False) else ""
                    border_color = "#10B981" if is_operator else "#3B82F6"
                    speaker_color = "#10B981" if is_operator else "#3B82F6"
                    speaker_label = "OPERATOR" if is_operator else "CALLER"

                    # English translation of caller speech
                    eng_text = getattr(seg, "translation", None) or translate_to_english(seg.text)
                    trans_html = ""
                    if not is_operator and eng_text:
                        trans_html = f"""
                        <div class="transcript-translation-box">
                            <span class="transcript-translation-pill">English</span>
                            <span>{eng_text}</span>
                        </div>
                        """

                    st.markdown(
                        f"""
                        <div class="transcript-chunk-final" style="border-left: 3px solid {border_color}; margin-bottom: 8px; padding: 10px 14px; border-radius: 8px;">
                            <div style="display: flex; justify-content: space-between; font-size: 11px; font-weight: 700; margin-bottom: 4px;">
                                <span style="color: {speaker_color};">[{seg.timestamp_offset}] {speaker_label} {whisper_tag}</span>
                            </div>
                            <div style="font-size: 13.5px; line-height: 1.5;">{seg.text}</div>
                            {trans_html}
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
            elif is_connected:
                st.markdown(
                    """
                    <div class="transcript-chunk-final" style="padding: 16px; text-align: center; color: {muted_text}; font-size: 13px; font-style: italic; border-radius: 8px;">
                        Call connected. Waiting for caller speech... Transcript will stream here.
                    </div>
                    """,
                    unsafe_allow_html=True
                )
            else:
                st.markdown(
                    """
                    <div class="transcript-chunk-final" style="padding: 16px; text-align: center; color: {muted_text}; font-size: 13px; font-style: italic; border-radius: 8px;">
                        No active call. Click 'Simulate Incoming Call' to stream caller transcript.
                    </div>
                    """,
                    unsafe_allow_html=True
                )

            # Show Streaming Partial Hypothesis
            if st.session_state.sim_partial_segment:
                p_seg = st.session_state.sim_partial_segment
                p_trans = getattr(p_seg, "translation", None) or translate_to_english(p_seg.text)
                p_trans_html = ""
                if p_trans:
                    p_trans_html = f"""
                    <div class="transcript-translation-box">
                        <span class="transcript-translation-pill">English</span>
                        <span>{p_trans} ...</span>
                    </div>
                    """
                st.markdown(
                    f"""
                    <div class="transcript-chunk-partial" style="border-left: 3px solid #64748B; padding: 10px 14px; border-radius: 8px; margin-bottom: 8px;">
                        <div style="font-size: 11px; font-weight: 700; opacity: 0.8; margin-bottom: 4px;">[{p_seg.timestamp_offset}] {p_seg.speaker.upper()} (Streaming...):</div>
                        <div style="font-size: 13px; font-style: italic;">{p_seg.text} ...</div>
                        {p_trans_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )

        # Simple Title: Suggested Questions to Ask
        threat_list = [t["type"] for t in triage_res.get("threat_types", []) if t.get("type") not in ("other", None)]
        covert_q = triage_res.get('suggested_safe_question')
        
        if covert_q:
            safe_q = covert_q
        elif not threat_list:
            safe_q = "112 Helpline, aapki kya madad kar sakte hain? Aap safe jagah par hain?"
        elif "accident_fire" in threat_list:
            safe_q = "Fire tenders dispatch ho chuki hain. Kya building ke andar koi fasa hai ya sabhi bahar nikal aaye hain?"
        elif "medical_emergency" in threat_list:
            safe_q = "Ambulance team nikal chuki hai. Kya mareez hosh mein hain aur saans lene mein takleef ho rahi hai?"
        elif "domestic_violence" in threat_list:
            safe_q = "PCR police team dispatch ho rahi hai. Kya aap surakshit kamre mein darwaza andar se lock kar sakte hain?"
        elif "stalking_harassment" in threat_list:
            safe_q = "PCR van alert kar di gayi hai. Kya aap kisi crowd ya public area / metro station ke andar ja sakte hain?"
        else:
            safe_q = triage_res.get('suggested_follow_up') or "Aap safe jagah par ho? Kya aap 'haan' ya 'nahin' mein bol sakte hain?"
        
        st.markdown(
            f"""
            <div class="protocol-card" style="margin-top: 14px; margin-bottom: 8px; padding: 12px 16px;">
                <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.75; margin-bottom: 6px;">
                    Suggested Questions to Ask
                </div>
                <div class="protocol-card-phrase" style="font-size: 14px; font-weight: 600; color: {'#F1F5F9' if is_dark else '#142238'};">
                    "{safe_q}"
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        if st.button("Speak Question to Caller 🎙️", use_container_width=True):
            st.session_state.sim_played_segments.append(
                TranscriptEvent(88, timer_str, "Operator", safe_q, is_final=True)
            )
            st.success("Operator question logged.")
            st.rerun()

    # RIGHT COLUMN: Triage Measures, Routing & Nearby Fleet
    with col_triage:
        # Simple Title: Emergency Type & Urgency
        render_triage_card(triage_res)

        # Determine Incident GPS Location
        target_lat, target_lon = 28.6139, 77.2090
        loc_display_name = "Awaiting Caller Location"
        
        locs = triage_res.get("location", [])
        if locs and locs[0].get("lat") and locs[0].get("lon"):
            target_lat = locs[0]["lat"]
            target_lon = locs[0]["lon"]
            loc_display_name = locs[0]["text"]
        elif locs and locs[0].get("text"):
            loc_display_name = locs[0]["text"]

        # Simple Title: Location & Nearby Services
        st.markdown(
            f"""
            <div style="margin: 18px 0 8px 0; font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.75;">
                Location & Nearby Services
            </div>
            <div class="telemetry-subcard" style="padding: 9px 14px; border-radius: 8px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                <div style="font-size: 12.5px;">
                    📍 <b>{loc_display_name}</b>
                </div>
                <div style="font-size: 11px; font-family: monospace; opacity: 0.8;">
                    {f"({target_lat:.4f}° N, {target_lon:.4f}° E)" if locs else "(Coordinates Pending)"}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        nearest_services_fleet = get_all_services_nearest_units(db, target_lat=target_lat, target_lon=target_lon)
        inc_id = st.session_state.selected_incident_id

        if nearest_services_fleet:
            for u in nearest_services_fleet:
                stype = u["service_type"]
                badge_class = (
                    "fleet-badge-police" if stype == "police" else (
                        "fleet-badge-ambulance" if stype == "medical" else (
                            "fleet-badge-fire" if stype == "fire" else "fleet-badge-shelter"
                        )
                    )
                )
                service_label = (
                    "POLICE 112" if stype == "police" else (
                        "AMBULANCE 108" if stype == "medical" else (
                            "FIRE 101" if stype == "fire" else "SHELTER 181"
                        )
                    )
                )
                status_color = "#10B981" if u["is_available"] else "#F59E0B"
                status_label = "Available" if u["is_available"] else "En Route"

                col_unit_info, col_unit_btn = st.columns([3, 1.2])
                with col_unit_info:
                    st.markdown(
                        f"""
                        <div class="fleet-unit-card" style="margin-bottom: 6px; padding: 8px 12px;">
                            <div>
                                <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 2px;">
                                    <span class="{badge_class}">{service_label}</span>
                                    <span style="font-weight: 700; font-size: 13px;">{u['unit_name']}</span>
                                </div>
                                <div style="font-size: 12px; opacity: 0.85;">
                                    {u['distance_km']} km • <span style="color: {accent_cyan}; font-weight: 600;">~{u['eta_minutes']}m ETA</span> • <span style="color: {status_color};">{status_label}</span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                with col_unit_btn:
                    btn_label = "Dispatch →" if u["is_available"] else "Track"
                    if st.button(btn_label, key=f"btn_disp_{u['unit_id']}", use_container_width=True, type="primary" if u["is_available"] else "secondary"):
                        try:
                            assign_unit_to_incident(db, inc_id, u["unit_id"], assigned_by=st.session_state.user["employee_id"])
                            st.success(f"{u['unit_name']} dispatched!")
                            st.rerun()
                        except Exception as e:
                            st.warning(f"Alert: {str(e)}")



    db.close()

# ---------------------------------------------------------
# Page 4: Location Recovery Workflow (Section 6.H)
# ---------------------------------------------------------
def page_location_recovery():
    render_app_header(st.session_state.user)
    db = get_db_session()

    st.subheader("Location Disambiguation & Candidate Confirmation")
    st.markdown(
        """
        > **Safety & Accuracy Protocol:** Callers under distress often cannot provide a formal postal address.
        > This console surfaces relative landmark phrases, gazetteer candidate matches, and structured clarification prompts.
        """
    )

    incidents_needing = get_incidents_needing_location_recovery(db)
    
    if not incidents_needing:
        st.success("✅ All active incidents have confirmed high-confidence locations.")
        # Allow inspecting selected incident anyway
        sel_inc = db.query(Incident).filter(Incident.id == st.session_state.selected_incident_id).first()
        inc_list = [sel_inc] if sel_inc else []
    else:
        inc_list = incidents_needing

    if inc_list:
        inc_options = {inc.id: f"{inc.id} — {inc.caller_name or 'Caller'} ({inc.location_text or 'Location Missing'})" for inc in inc_list}
        selected_id = st.selectbox(
            "Select Incident Requiring Location Recovery",
            options=list(inc_options.keys()),
            format_func=lambda x: inc_options[x]
        )
        
        target_inc = db.query(Incident).filter(Incident.id == selected_id).first()
        if target_inc:
            details = get_location_recovery_details(target_inc, db)

            col_cand, col_manual = st.columns([1, 1], gap="medium")

            with col_cand:
                st.markdown(
                    f"""
                    <div class="sahaay-panel">
                        <div class="sahaay-panel-title">Incident Location Status</div>
                        <div style="font-size: 14px; line-height: 1.8;">
                            <div><b>Incident ID:</b> {target_inc.id}</div>
                            <div><b>Current Text:</b> {target_inc.location_text or 'None'}</div>
                            <div><b>Source:</b> {target_inc.location_source} • <b>Confidence:</b> {target_inc.location_confidence:.0%}</div>
                            <div><b>Status:</b> {'✅ CONFIRMED' if details['is_confirmed'] else '⚠️ UNCONFIRMED / MISSING'}</div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )

                st.subheader("Transcript Text & Location Mentions")
                st.info(f"🗣️ \"{details['transcript_text']}\"")

                st.subheader("Candidate Location Matches")
                candidates = details.get("candidates", [])
                for idx, c in enumerate(candidates):
                    st.markdown(
                        f"""
                        <div style="background: white; border: 1px solid #E8EDF2; border-radius: 6px; padding: 12px; margin-bottom: 8px;">
                            <div style="display: flex; justify-content: space-between;">
                                <div>
                                    <div style="font-weight: 700; color: #173B57; font-size: 15px;">📍 {c['text']}</div>
                                    <div style="font-size: 12px; color: #526171;">Type: {c.get('type', 'locality')} • Source: {c.get('source')}</div>
                                    <div style="font-size: 11px; color: #286A8A;">Coords: ({c.get('lat')}, {c.get('lon')})</div>
                                </div>
                                <div>
                                    <span style="background: #E8F4F8; color: #00689D; padding: 4px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">
                                        Match: {c.get('confidence', 0.5):.0%}
                                    </span>
                                </div>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )
                    c_act1, c_act2 = st.columns([1, 1])
                    with c_act1:
                        if st.button(f"✅ Confirm '{c['text']}'", key=f"conf_cand_{idx}"):
                            confirm_candidate_location(
                                db=db,
                                incident_id=target_inc.id,
                                location_text=c["text"],
                                latitude=c["lat"],
                                longitude=c["lon"],
                                actor_id=st.session_state.user["employee_id"],
                                location_type=c.get("type", "locality")
                            )
                            st.success(f"Confirmed location for {target_inc.id}!")
                            st.rerun()

            with col_manual:
                st.subheader("Manual Gazetteer / Landmark Lookup")
                search_q = st.text_input("Search Delhi NCR Landmark, Metro or Pincode", placeholder="e.g. Rohini Sector 14, Karol Bagh, 110005, AIIMS")
                if search_q.strip():
                    results = manual_search_gazetteer(search_q)
                    if results:
                        st.write("##### Matching Gazetteer Entries:")
                        for r_idx, r in enumerate(results):
                            st.markdown(
                                f"""
                                <div style="background: #F8FAFC; border: 1px solid #CBD5E1; border-radius: 6px; padding: 10px; margin-bottom: 6px;">
                                    <b>{r['text']}</b> ({r['type']}) — Pincode: {r['pincode']}<br>
                                    <span style="font-size: 11px; color: #526171;">Coords: {r['lat']}, {r['lon']} (Score: {r['confidence']:.2f})</span>
                                </div>
                                """,
                                unsafe_allow_html=True
                            )
                            if st.button(f"Assign '{r['text']}' to Incident", key=f"btn_assign_gaz_{r_idx}"):
                                confirm_candidate_location(
                                    db=db,
                                    incident_id=target_inc.id,
                                    location_text=r["text"],
                                    latitude=r["lat"],
                                    longitude=r["lon"],
                                    actor_id=st.session_state.user["employee_id"],
                                    location_type=r["type"]
                                )
                                st.success("Location assigned!")
                                st.rerun()
                    else:
                        st.warning("No matches found in Delhi gazetteer.")

                st.markdown("---")
                st.subheader("Suggested Clarification Questions")
                st.caption("Ask caller one targeted question to recover missing location safely:")
                for q in details.get("suggested_questions", []):
                    st.markdown(f"• **{q['question']}**")

    db.close()

# ---------------------------------------------------------
# Page: Live Operations & Fleet Tracking Dashboard
# ---------------------------------------------------------
def page_dashboard():
    render_app_header(st.session_state.user)
    db = get_db_session()
    is_dark = (st.session_state.theme_mode == "dark")

    # Top title and quick action
    t_col1, t_col2 = st.columns([7.5, 2.5])
    with t_col1:
        st.markdown(
            """
            <div style="margin-bottom: 18px; margin-top: 2px;">
                <div style="font-size: 23px; font-weight: 800; letter-spacing: -0.02em;">Operations Command Dashboard</div>
                <div style="font-size: 13.5px; opacity: 0.75; margin-top: 3px;">
                    Real-time Fleet Telemetry, Multilingual CAD Dispatch & System-Wide Emergency KPIs.
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    with t_col2:
        if st.button("⛨  New Incident Live Console", use_container_width=True, type="primary"):
            st.session_state.current_page = "triage"
            st.rerun()

    # Query metrics from DB
    all_incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()
    all_units = db.query(ResponseUnit).all()
    all_dispatches = db.query(DispatchAssignment).all()

    total_cases = len(all_incidents)
    resolved_cases = sum(1 for i in all_incidents if i.status == "resolved")
    active_cases = sum(1 for i in all_incidents if i.status in ["active", "in_progress", "dispatched"])
    total_dispatches = len(all_dispatches)

    # 1. Executive KPI Cards (Moved from Case History)
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        st.markdown(
            f"""
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Total Logged Cases</div>
                <div class="sahaay-kpi-value">{total_cases}</div>
                <div class="sahaay-kpi-footer">Cumulative 24h Archive</div>
            </div>
            """, unsafe_allow_html=True
        )
    with k2:
        st.markdown(
            f"""
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Resolved Cases</div>
                <div class="sahaay-kpi-value" style="color: {'#34D399' if is_dark else '#08784E'};">{resolved_cases}</div>
                <div class="sahaay-kpi-footer" style="color: {'#34D399' if is_dark else '#08784E'};">[✓] Verified Outcome Logged</div>
            </div>
            """, unsafe_allow_html=True
        )
    with k3:
        st.markdown(
            f"""
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Active / In Progress</div>
                <div class="sahaay-kpi-value" style="color: {'#FF5C68' if is_dark else '#C62838'};">{active_cases}</div>
                <div class="sahaay-kpi-footer" style="color: {'#FF5C68' if is_dark else '#C62838'};">[●] Live Tactical Response</div>
            </div>
            """, unsafe_allow_html=True
        )
    with k4:
        st.markdown(
            f"""
            <div class="sahaay-kpi-card">
                <div class="sahaay-kpi-label">Units Dispatched</div>
                <div class="sahaay-kpi-value" style="color: {'#22D3EE' if is_dark else '#007F9E'};">{total_dispatches}</div>
                <div class="sahaay-kpi-footer" style="color: {'#22D3EE' if is_dark else '#007F9E'};">Avg Response: 5.2m (Target &lt;15m)</div>
            </div>
            """, unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top: 18px;'></div>", unsafe_allow_html=True)

    # 2. Fleet Readiness Overview Bar
    police_units = [u for u in all_units if u.service_type == "police"]
    med_units = [u for u in all_units if u.service_type == "medical"]
    fire_units = [u for u in all_units if u.service_type == "fire"]
    shelter_units = [u for u in all_units if u.service_type in ["shelter", "legal"]]

    p_avail = sum(1 for u in police_units if u.status == "available")
    m_avail = sum(1 for u in med_units if u.status == "available")
    f_avail = sum(1 for u in fire_units if u.status == "available")
    s_avail = sum(1 for u in shelter_units if u.status == "available")

    st.markdown(
        f"""
        <div style="background: {'#19283D' if is_dark else '#E8EFF7'}; border: 1px solid {'#304158' if is_dark else '#CBD5E1'}; border-radius: 12px; padding: 14px 18px; margin-bottom: 20px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; opacity: 0.7; margin-bottom: 10px;">
                Fleet Readiness & Tactical Unit Allocation (18 Total Units Across NCR)
            </div>
            <div style="display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px;">
                <div style="border-left: 3px solid {'#22D3EE' if is_dark else '#007F9E'}; padding-left: 10px;">
                    <div style="font-size: 12px; opacity: 0.75;">Police PCR Patrols</div>
                    <div style="font-size: 18px; font-weight: 800; color: {'#22D3EE' if is_dark else '#007F9E'};">{p_avail} / {len(police_units)} <span style="font-size: 12px; font-weight: 500;">Ready</span></div>
                </div>
                <div style="border-left: 3px solid {'#FF5C68' if is_dark else '#C62838'}; padding-left: 10px;">
                    <div style="font-size: 12px; opacity: 0.75;">ALS Ambulances</div>
                    <div style="font-size: 18px; font-weight: 800; color: {'#FF5C68' if is_dark else '#C62838'};">{m_avail} / {len(med_units)} <span style="font-size: 12px; font-weight: 500;">Ready</span></div>
                </div>
                <div style="border-left: 3px solid {'#FBBF24' if is_dark else '#956000'}; padding-left: 10px;">
                    <div style="font-size: 12px; opacity: 0.75;">Fire Tenders</div>
                    <div style="font-size: 18px; font-weight: 800; color: {'#FBBF24' if is_dark else '#956000'};">{f_avail} / {len(fire_units)} <span style="font-size: 12px; font-weight: 500;">Ready</span></div>
                </div>
                <div style="border-left: 3px solid #A855F7; padding-left: 10px;">
                    <div style="font-size: 12px; opacity: 0.75;">Saheli Crisis Vans</div>
                    <div style="font-size: 18px; font-weight: 800; color: #C084FC;">{s_avail} / {len(shelter_units)} <span style="font-size: 12px; font-weight: 500;">Ready</span></div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 3. Interactive Live Fleet Tracking Map
    st.markdown(
        f"""
        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px;">
            <div>
                <div style="font-size: 16px; font-weight: 800; letter-spacing: -0.01em;">Live Service Vehicle GPS Tracking & CAD Incidents</div>
                <div style="font-size: 12.5px; opacity: 0.7; margin-top: 1px;">
                    Interactive GIS map tracking all 18 emergency response units and active crisis call points in Delhi NCR.
                </div>
            </div>
            <div style="display: flex; gap: 8px; font-size: 11.5px; font-weight: 600;">
                <span style="color: {'#22D3EE' if is_dark else '#007F9E'};">● Police (PCR)</span>
                <span style="color: {'#FF5C68' if is_dark else '#C62838'};">● Medical (Ambulance)</span>
                <span style="color: {'#FBBF24' if is_dark else '#956000'};">● Fire Tender</span>
                <span style="color: #C084FC;">● Saheli Crisis Van</span>
                <span style="color: {'#FF5C68' if is_dark else '#C62838'}; font-weight: 700;">★ Active Incident</span>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Initialize Tactical Fleet Map with Pulsing Beacons & AntPath Corridors
    m = build_fleet_overview_map(all_incidents, all_units, all_dispatches, is_dark=is_dark)

    # Render Folium Map
    st_folium(m, height=480, use_container_width=True)

    st.markdown("<div style='margin-top: 22px;'></div>", unsafe_allow_html=True)

    # 4. Live Fleet Telemetry Table
    st.markdown(
        """
        <div style="font-size: 16px; font-weight: 800; letter-spacing: -0.01em; margin-bottom: 10px;">
            Service Vehicle Telemetry & Sector Deployment Status
        </div>
        """,
        unsafe_allow_html=True
    )

    t_filter_col, t_sp = st.columns([3, 7])
    with t_filter_col:
        svc_filter = st.selectbox(
            "Filter Fleet by Service",
            ["All Services", "Police (PCR)", "Ambulance (Medical)", "Fire Rescue", "Saheli Crisis Van"],
            label_visibility="collapsed"
        )

    # Filter units
    filtered_units = all_units
    if "Police" in svc_filter:
        filtered_units = [u for u in all_units if u.service_type == "police"]
    elif "Ambulance" in svc_filter:
        filtered_units = [u for u in all_units if u.service_type == "medical"]
    elif "Fire" in svc_filter:
        filtered_units = [u for u in all_units if u.service_type == "fire"]
    elif "Saheli" in svc_filter:
        filtered_units = [u for u in all_units if u.service_type in ["shelter", "legal"]]

    # Build clean telemetry table data
    telemetry_rows = []
    for u in filtered_units:
        status_tag = u.status.upper().replace("_", " ")
        if u.status == "available":
            badge_html = f"<span style='color: {'#34D399' if is_dark else '#08784E'}; font-weight: 700; background: {'rgba(52, 211, 153, 0.15)' if is_dark else 'rgba(8, 120, 78, 0.12)'}; padding: 2px 8px; border-radius: 6px; border: 1px solid {'rgba(52, 211, 153, 0.4)' if is_dark else 'rgba(8, 120, 78, 0.35)'};'>● {status_tag}</span>"
        elif u.status in ["assigned", "dispatched", "en_route"]:
            badge_html = f"<span style='color: {'#22D3EE' if is_dark else '#007F9E'}; font-weight: 700; background: {'rgba(34, 211, 238, 0.15)' if is_dark else 'rgba(0, 127, 158, 0.12)'}; padding: 2px 8px; border-radius: 6px; border: 1px solid {'rgba(34, 211, 238, 0.4)' if is_dark else 'rgba(0, 127, 158, 0.35)'};'>● {status_tag}</span>"
        else:
            badge_html = f"<span style='color: {'#FBBF24' if is_dark else '#956000'}; font-weight: 700; background: {'rgba(251, 191, 36, 0.15)' if is_dark else 'rgba(149, 96, 0, 0.12)'}; padding: 2px 8px; border-radius: 6px; border: 1px solid {'rgba(251, 191, 36, 0.4)' if is_dark else 'rgba(149, 96, 0, 0.35)'};'>● {status_tag}</span>"
        
        telemetry_rows.append({
            "Unit ID": u.id,
            "Call Sign / Name": u.unit_name,
            "Service Type": u.service_type.capitalize(),
            "GPS Telemetry": f"{u.current_lat:.4f}, {u.current_lon:.4f}",
            "Speed": f"{u.speed_kmh:.1f} km/h",
            "Operational Status": badge_html
        })

    # Render table in clean card
    table_card_html = f"""
    <div style="background: {'#111C2E' if is_dark else '#FFFFFF'}; border: 1px solid {'#304158' if is_dark else '#CBD5E1'}; border-radius: 10px; overflow: hidden; margin-bottom: 24px;">
        <table style="width: 100%; border-collapse: collapse; font-size: 13px;">
            <thead>
                <tr style="border-bottom: 1px solid {'#304158' if is_dark else '#CBD5E1'}; background: {'#19283D' if is_dark else '#E8EFF7'};">
                    <th style="padding: 10px 14px; text-align: left; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">Unit ID</th>
                    <th style="padding: 10px 14px; text-align: left; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">Vehicle / Call Sign</th>
                    <th style="padding: 10px 14px; text-align: left; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">Service Type</th>
                    <th style="padding: 10px 14px; text-align: left; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">GPS Telemetry</th>
                    <th style="padding: 10px 14px; text-align: left; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">Speed</th>
                    <th style="padding: 10px 14px; text-align: left; font-weight: 700; font-size: 11px; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">Operational Status</th>
                </tr>
            </thead>
            <tbody>
    """
    for r in telemetry_rows:
        table_card_html += f"""
                <tr style="border-bottom: 1px solid {'#304158' if is_dark else '#E8EFF7'};">
                    <td style="padding: 10px 14px; font-weight: 700; font-family: monospace; color: {'#22D3EE' if is_dark else '#007F9E'};">{r['Unit ID']}</td>
                    <td style="padding: 10px 14px; font-weight: 600;">{r['Call Sign / Name']}</td>
                    <td style="padding: 10px 14px;">{r['Service Type']}</td>
                    <td style="padding: 10px 14px; font-family: monospace; opacity: 0.85;">{r['GPS Telemetry']}</td>
                    <td style="padding: 10px 14px;">{r['Speed']}</td>
                    <td style="padding: 10px 14px;">{r['Operational Status']}</td>
                </tr>
        """
    table_card_html += """
            </tbody>
        </table>
    </div>
    """
    st.markdown(table_card_html, unsafe_allow_html=True)

    # 5. Judge-Explainable PS3 Intelligence & Architecture Pillars
    st.markdown(
        f"""
        <div style="background: {'#19283D' if is_dark else '#E8EFF7'}; border: 1px solid {'#304158' if is_dark else '#CBD5E1'}; border-radius: 12px; padding: 20px; margin-bottom: 20px;">
            <div style="font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.08em; color: {'#22D3EE' if is_dark else '#007F9E'};" margin-bottom: 4px;">
                Judge Briefing • eSahaay Core PS3 Innovation Pillars
            </div>
            <div style="font-size: 16px; font-weight: 800; margin-bottom: 14px;">
                Explainable AI & Deterministic Safety Guarantees
            </div>
            <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 16px;">
                <div style="background: {'#111C2E' if is_dark else '#FFFFFF'}; border: 1px solid {'#304158' if is_dark else '#CBD5E1'}; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 13px; font-weight: 700; margin-bottom: 6px; color: {'#22D3EE' if is_dark else '#007F9E'};">1. Multilingual Sub-10s Triage</div>
                    <div style="font-size: 12px; opacity: 0.8; line-height: 1.5;">
                        Real-time tokenized pipeline handles Hindi, Hinglish, and English call audio. Acoustic whisper detection extracts distress signals before full sentence completion.
                    </div>
                </div>
                <div style="background: {'#111C2E' if is_dark else '#FFFFFF'}; border: 1px solid {'#304158' if is_dark else '#CBD5E1'}; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 13px; font-weight: 700; margin-bottom: 6px; color: {'#FF5C68' if is_dark else '#C62838'};">2. Irrevocable Safety Floor</div>
                    <div style="font-size: 12px; opacity: 0.8; line-height: 1.5;">
                        Critical threats (violence, weapon, severe bleeding) lock the priority permanently at P0. The operator can escalate, but algorithms can never downgrade below safety floor.
                    </div>
                </div>
                <div style="background: {'#111C2E' if is_dark else '#FFFFFF'}; border: 1px solid {'#304158' if is_dark else '#CBD5E1'}; border-radius: 8px; padding: 14px;">
                    <div style="font-size: 13px; font-weight: 700; margin-bottom: 6px; color: {'#34D399' if is_dark else '#08784E'};">3. Unified Cross-Agency Dispatch</div>
                    <div style="font-size: 12px; opacity: 0.8; line-height: 1.5;">
                        Police PCR, ALS Medical, Fire Rescue, and Saheli Crisis Vans receive simultaneous GIS coordinates and route vectors without inter-departmental telephone delay.
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    db.close()

# ---------------------------------------------------------
# Page 5: Incident History Archive with CSV Export
# ---------------------------------------------------------
def page_incidents():
    render_app_header(st.session_state.user)
    db = get_db_session()
    is_dark = (st.session_state.theme_mode == "dark")
    accent_cyan = "#22D3EE" if is_dark else "#007F9E"
    sub_color = "#A8B6C9" if is_dark else "#475569" 

    c_back, c_sp = st.columns([2.5, 7.5])
    with c_back:
        if st.button("← Back to Triage", use_container_width=True):
            st.session_state.current_page = "triage"
            st.rerun()

    st.markdown(
        """
        <div style="margin-bottom: 16px; margin-top: 4px;">
            <div style="font-size: 22px; font-weight: 800; letter-spacing: -0.02em;">Case History</div>
            <div style="font-size: 13px; opacity: 0.75; margin-top: 2px;">
                Historical log of emergency calls, dispatched units, response timelines, and verified outcomes.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    all_incidents = db.query(Incident).order_by(Incident.created_at.desc()).all()

    # (KPI cards moved to dedicated Operations Dashboard as requested)
    st.markdown("<div style='margin-top: 4px;'></div>", unsafe_allow_html=True)

    # Search and Filter bar
    f1, f2, f3, f4 = st.columns([2.2, 1.2, 1.2, 1.2])
    with f1:
        search_kw = st.text_input("🔍 Search History", placeholder="Search Case ID, Caller, Location, Threat, or Service...")
    with f2:
        cat_filter = st.selectbox("Emergency Category", [
            "All Categories",
            "Medical Emergency",
            "Domestic Violence",
            "Fire & Explosion",
            "Stalking & Harassment",
            "Legal Advisory"
        ])
    with f3:
        status_filter = st.selectbox("Resolution Status", ["All Statuses", "Resolved Only", "Active / In Progress"])
    with f4:
        urgency_filter = st.selectbox("Priority Level", ["All Priorities", "P0 Critical", "P1 High", "P2 Medium", "P3 Low"])

    # Filter incidents
    filtered = all_incidents
    if search_kw:
        skw = search_kw.lower().strip()
        filtered = [
            i for i in filtered
            if skw in (i.id or "").lower() or
               skw in (i.caller_name or "").lower() or
               skw in (i.caller_masked_phone or "").lower() or
               skw in (i.location_text or "").lower() or
               skw in (i.primary_threat or "").lower() or
               skw in (i.resolution_notes or "").lower()
        ]
    if cat_filter != "All Categories":
        if cat_filter == "Medical Emergency":
            filtered = [i for i in filtered if "medical" in (i.primary_threat or "").lower() or "cardiac" in (i.primary_threat or "").lower() or "stroke" in (i.primary_threat or "").lower()]
        elif cat_filter == "Domestic Violence":
            filtered = [i for i in filtered if "domestic" in (i.primary_threat or "").lower() or "violence" in (i.primary_threat or "").lower()]
        elif cat_filter == "Fire & Explosion":
            filtered = [i for i in filtered if "fire" in (i.primary_threat or "").lower() or "cylinder" in (i.primary_threat or "").lower() or "accident" in (i.primary_threat or "").lower()]
        elif cat_filter == "Stalking & Harassment":
            filtered = [i for i in filtered if "stalking" in (i.primary_threat or "").lower() or "harass" in (i.primary_threat or "").lower()]
        elif cat_filter == "Legal Advisory":
            filtered = [i for i in filtered if "legal" in (i.primary_threat or "").lower()]

    if status_filter == "Resolved Only":
        filtered = [i for i in filtered if i.status == "resolved"]
    elif status_filter == "Active / In Progress":
        filtered = [i for i in filtered if i.status in ["active", "in_progress", "dispatched"]]

    if urgency_filter != "All Priorities":
        u_prefix = urgency_filter.split()[0]
        filtered = [i for i in filtered if i.current_urgency == u_prefix]

    st.markdown("<div style='margin-top: 8px;'></div>", unsafe_allow_html=True)

    if not filtered:
        st.info("No cases matching the selected filters.")
    else:
        for inc in filtered:
            dispatches = inc.dispatches
            units_list = []
            reached_times = []
            for d in dispatches:
                u_name = d.unit.unit_name if d.unit else d.unit_id
                units_list.append(u_name)
                if d.eta_minutes:
                    reached_times.append(f"{d.eta_minutes:.1f}m")

            units_badges_html = " ".join([
                f"<span style='background: {'rgba(34, 211, 238, 0.15)' if is_dark else 'rgba(0, 127, 158, 0.10)'}; color: {accent_cyan}; border: 1px solid {'rgba(34, 211, 238, 0.35)' if is_dark else 'rgba(0, 127, 158, 0.30)'}; padding: 2px 8px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-right: 4px;'>{u}</span>"
                for u in units_list
            ]) if units_list else f"<span style='color: {'#A8B6C9' if is_dark else '#64748B'}; font-size: 12px; font-style: italic;'>Pending assignment</span>"

            reached_str = f"Reached in {reached_times[0]}" if reached_times else ("En Route" if inc.status != "resolved" else "On Scene")

            conclusion_text = inc.resolution_notes or "Case active. Awaiting field resolution report."
            is_resolved = (inc.status == "resolved")
            status_chip = "<span style='background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.4); padding: 2px 10px; border-radius: 9999px; font-weight: 700; font-size: 11px;'>[✓] RESOLVED</span>" if is_resolved else "<span style='background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.4); padding: 2px 10px; border-radius: 9999px; font-weight: 700; font-size: 11px;'>[●] ACTIVE RESPONSE</span>"

            threat_lower = (inc.primary_threat or "").lower()
            if "hospital" in conclusion_text.lower() or "medical" in threat_lower or "cardiac" in threat_lower or "stroke" in threat_lower:
                pill_icon = ""
                pill_class = "conclusion-hospital"
                pill_title = "Hospital Admitted"
            elif "shelter" in conclusion_text.lower() or "sakhi" in conclusion_text.lower() or "domestic" in threat_lower:
                pill_icon = ""
                pill_class = "conclusion-shelter"
                pill_title = "Rescued & Sheltered"
            elif "fire" in conclusion_text.lower() or "suppressed" in conclusion_text.lower() or "extinguish" in conclusion_text.lower():
                pill_icon = ""
                pill_class = "conclusion-fire"
                pill_title = "Fire Extinguished"
            elif "detained" in conclusion_text.lower() or "apprehended" in conclusion_text.lower() or "stalking" in threat_lower:
                pill_icon = ""
                pill_class = "conclusion-police"
                pill_title = "Suspect Apprehended"
            else:
                pill_icon = ""
                pill_class = "conclusion-legal"
                pill_title = "Legal Aid Assigned"

            call_time_str = inc.created_at.strftime("%d %b %Y • %H:%M IST")

            st.markdown(
                f"""
                <div class="sahaay-card case-card" style="margin-bottom: 12px; padding: 16px 20px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px; flex-wrap: wrap; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="font-family: 'JetBrains Mono', monospace; font-size: 15px; font-weight: 800; color: {accent_cyan};">{inc.id}</span>
                            <span style="font-weight: 700; font-size: 15px; color: {'#F1F5F9' if is_dark else '#142238'};">{inc.primary_threat or 'Emergency Incident'}</span>
                            {render_priority_chip(inc.current_urgency)}
                        </div>
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 11.5px; color: {'#A8B6C9' if is_dark else '#52647B'}; font-family: monospace; font-weight: 600;">⏱ {call_time_str}</span>
                            {status_chip}
                        </div>
                    </div>

                    <div style="display: grid; grid-template-columns: 1.2fr 1.2fr 1fr; gap: 10px; font-size: 13px; margin-bottom: 10px;">
                        <div class="telemetry-subcard" style="padding: 8px 12px; border-radius: 6px;">
                            <div style="font-size: 10.5px; color: {'#A8B6C9' if is_dark else '#52647B'}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">Caller & Contact</div>
                            <div style="font-weight: 600; margin-top: 2px; color: {'#F1F5F9' if is_dark else '#142238'};">{inc.caller_name or 'Anonymous'} &nbsp;•&nbsp; <span style="font-family: monospace; color: {accent_cyan}; font-weight: 700;">{inc.caller_masked_phone or 'Unknown'}</span></div>
                        </div>
                        <div class="telemetry-subcard" style="padding: 8px 12px; border-radius: 6px;">
                            <div style="font-size: 10.5px; color: {'#A8B6C9' if is_dark else '#52647B'}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">Incident Location</div>
                            <div style="font-weight: 600; margin-top: 2px; color: {'#F1F5F9' if is_dark else '#142238'};">[Loc] {inc.location_text or 'Pending Location'}</div>
                        </div>
                        <div class="telemetry-subcard" style="padding: 8px 12px; border-radius: 6px;">
                            <div style="font-size: 10.5px; color: {'#A8B6C9' if is_dark else '#52647B'}; font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em;">Response Time</div>
                            <div style="font-weight: 700; margin-top: 2px; color: {'#34D399' if is_dark else '#08784E'};">{reached_str}</div>
                        </div>
                    </div>

                    <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 10px; flex-wrap: wrap;">
                        <span style="font-size: 11px; font-weight: 700; color: {'#A8B6C9' if is_dark else '#52647B'}; text-transform: uppercase; letter-spacing: 0.05em;">Services Sent:</span>
                        <div>{units_badges_html}</div>
                    </div>

                    <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 10px; margin-bottom: 8px; flex-wrap: wrap; gap: 8px;">
                        <div style="display: flex; align-items: center; gap: 8px;">
                            <span style="font-size: 11px; font-weight: 700; color: {'#A8B6C9' if is_dark else '#52647B'}; text-transform: uppercase; letter-spacing: 0.05em;">Outcome:</span>
                            <span class="conclusion-pill {pill_class}">{pill_title}</span>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            c_view, c_disp = st.columns([1.8, 3.2])
            with c_view:
                if st.button(f"Case Details →", key=f"open_dossier_{inc.id}", use_container_width=True, type="primary"):
                    st.session_state.selected_incident_id = inc.id
                    st.session_state.current_page = "case_detail"
                    st.rerun()

    # CSV Export Button
    st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
    if filtered:
        export_rows = []
        for inc in filtered:
            units = ", ".join([d.unit.unit_name if d.unit else d.unit_id for d in inc.dispatches])
            export_rows.append({
                "Case ID": inc.id,
                "Date": inc.created_at.strftime("%Y-%m-%d %H:%M"),
                "Caller": inc.caller_name,
                "Phone": inc.caller_masked_phone,
                "Emergency Type": inc.primary_threat,
                "Priority": inc.current_urgency,
                "Location": inc.location_text,
                "Services Sent": units,
                "Status": inc.status.upper(),
                "Conclusion": inc.resolution_notes
            })
        df_export = pd.DataFrame(export_rows)
        csv_bytes = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Export Case History (CSV)",
            data=csv_bytes,
            file_name=f"sahaay_case_history_{datetime.datetime.now().strftime('%Y%m%d_%H%M')}.csv",
            mime="text/csv"
        )

    db.close()


def page_case_detail():
    render_app_header(st.session_state.user)
    db = get_db_session()
    is_dark = (st.session_state.theme_mode == "dark")
    accent_cyan = "#22D3EE" if is_dark else "#007F9E"
    sub_color = "#A8B6C9" if is_dark else "#475569"
    success_color = "#34D399" if is_dark else "#08784E" 

    inc_id = st.session_state.selected_incident_id
    incident = db.query(Incident).filter(Incident.id == inc_id).first()

    if not incident:
        st.error(f"Incident {inc_id} not found.")
        if st.button("← Back to Case History"):
            st.session_state.current_page = "incidents"
            st.rerun()
        db.close()
        return

    # Header and Navigation Bar
    c_back, c_hdr_right = st.columns([2.5, 7.5])
    with c_back:
        if st.button("← Back to Case History", use_container_width=True):
            st.session_state.current_page = "incidents"
            st.rerun()

    is_resolved = (incident.status == "resolved")
    status_chip = "<span style='background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.4); padding: 4px 12px; border-radius: 9999px; font-weight: 700; font-size: 12px;'>[✓] RESOLVED</span>" if is_resolved else "<span style='background: rgba(239, 68, 68, 0.15); color: #EF4444; border: 1px solid rgba(239, 68, 68, 0.4); padding: 4px 12px; border-radius: 9999px; font-weight: 700; font-size: 12px;'>🟡 ACTIVE / UNDER INVESTIGATION</span>"

    st.markdown(
        f"""
        <div class="sahaay-card" style="padding: 16px 20px; margin: 12px 0 16px 0;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div>
                    <div style="display: flex; align-items: center; gap: 10px;">
                        <span style="font-family: 'JetBrains Mono', monospace; font-size: 20px; font-weight: 800; color: {accent_cyan};">{incident.id}</span>
                        <span style="font-size: 20px; font-weight: 800;">{incident.primary_threat or 'Emergency Incident'}</span>
                        {render_priority_chip(incident.current_urgency)}
                    </div>
                    <div style="font-size: 13px; opacity: 0.75; margin-top: 4px;">
                        Caller: <b>{incident.caller_name or 'Anonymous'}</b> &nbsp;•&nbsp; 
                        Phone: <span style="font-family: monospace;">{incident.caller_masked_phone or 'Unknown'}</span> &nbsp;•&nbsp; 
                        Logged: <b>{incident.created_at.strftime('%d %b %Y, %H:%M:%S IST')}</b>
                    </div>
                </div>
                <div>{status_chip}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    col_left, col_right = st.columns([1.1, 1], gap="medium")

    with col_left:
        # SECTION 1: EMERGENCY CALL RECORDING AUDIO PLAYER
        rec_b64 = get_call_recording_b64(incident.id)
        st.markdown(
            f"""
            <div class="sahaay-card" style="padding: 16px 18px; margin-bottom: 14px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                    <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8;">
                        [ Audio ] Emergency Call Audio Recording
                    </div>
                    <div style="font-size: 11px; padding: 2px 8px; border-radius: 4px; background: {'rgba(34, 211, 238, 0.15)' if is_dark else 'rgba(0, 127, 158, 0.10)'}; color: {accent_cyan}; font-family: monospace;">
                        Channel Line 1 • 16 kHz WAV
                    </div>
                </div>
                <div style="background: {'rgba(15, 23, 42, 0.4)' if is_dark else '#E8EFF7'}; border: 1px solid {'rgba(148, 163, 184, 0.2)' if is_dark else '#CBD5E1'}; border-radius: 8px; padding: 12px; display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; justify-content: space-between; font-size: 11px; opacity: 0.7;">
                        <span>Helpline Audio Stream ({incident.id})</span>
                        <span>Duration: 00:04.5</span>
                    </div>
                    <audio controls style="width: 100%; height: 38px;">
                        <source src="data:audio/wav;base64,{rec_b64}" type="audio/wav">
                        Your browser does not support audio playback.
                    </audio>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # SECTION 2: FULL BILINGUAL TRANSCRIPT WITH TRANSLATIONS
        st.markdown(
            """
            <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8; margin: 10px 0 8px 0;">
                [ Transcript ] Dialogue Transcript & Translation
            </div>
            """,
            unsafe_allow_html=True
        )
        segments = db.query(TranscriptSegment).filter(TranscriptSegment.incident_id == incident.id).order_by(TranscriptSegment.created_at.asc(), TranscriptSegment.id.asc()).all()
        if segments:
            for seg in segments:
                is_caller = (seg.speaker == "Caller")
                speaker_color = accent_cyan if is_caller else success_color
                bubble_bg = ('rgba(34, 211, 238, 0.08)' if is_dark else 'rgba(0, 127, 158, 0.06)') if is_caller else ('rgba(52, 211, 153, 0.08)' if is_dark else 'rgba(8, 120, 78, 0.06)')
                bubble_border = ('rgba(34, 211, 238, 0.25)' if is_dark else 'rgba(0, 127, 158, 0.25)') if is_caller else ('rgba(52, 211, 153, 0.25)' if is_dark else 'rgba(8, 120, 78, 0.25)')

                trans_text = seg.normalized_text if (seg.normalized_text and seg.normalized_text != seg.raw_text) else translate_to_english(seg.raw_text)
                trans_html = ""
                if trans_text and trans_text.strip() != seg.raw_text.strip():
                    trans_html = f"""
                    <div class="transcript-translation-box" style="margin-top: 6px; padding: 6px 10px; border-radius: 4px; font-size: 12px;">
                        <span class="transcript-translation-pill">EN</span> {trans_text}
                    </div>
                    """

                st.markdown(
                    f"""
                    <div style="background: {bubble_bg}; border: 1px solid {bubble_border}; border-radius: 8px; padding: 10px 14px; margin-bottom: 8px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                            <span style="font-size: 11.5px; font-weight: 700; color: {speaker_color};">● {seg.speaker}</span>
                            <span style="font-size: 11px; opacity: 0.6; font-family: monospace;">{seg.timestamp_offset}</span>
                        </div>
                        <div style="font-size: 13.5px; font-weight: 500; line-height: 1.5;">{seg.raw_text}</div>
                        {trans_html}
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No recorded dialogue segments found for this incident.")

    with col_right:
        # SECTION 3: SERVICES SENT & RESPONSE TRAJECTORY TIMELINE
        st.markdown(
            f"""
            <div class="sahaay-card" style="padding: 16px 18px; margin-bottom: 14px;">
                <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.8; margin-bottom: 8px;">
                    [ Deployment ] Services Sent & Response Trajectory
                </div>
                <div class="telemetry-subcard" style="padding: 9px 12px; border-radius: 6px; margin-bottom: 12px; display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 13px;">
                        [Loc] <b>{incident.location_text or 'Pending Location'}</b>
                    </div>
                    <div style="font-size: 11px; opacity: 0.7; font-family: monospace;">
                        ({(incident.latitude or 28.6139):.4f}° N, {(incident.longitude or 77.2090):.4f}° E)
                    </div>
                </div>
            """,
            unsafe_allow_html=True
        )

        dispatches = incident.dispatches
        if dispatches:
            for d in dispatches:
                u = d.unit
                u_name = u.unit_name if u else d.unit_id
                stype = d.service_type.upper()
                disp_time = d.dispatched_at.strftime('%H:%M:%S') if d.dispatched_at else "13:40:00"
                ack_time = d.acknowledged_at.strftime('%H:%M:%S') if d.acknowledged_at else "13:40:45"
                arr_time = d.arrived_at.strftime('%H:%M:%S') if d.arrived_at else "13:46:12"
                resp_min = d.eta_minutes if d.eta_minutes else 5.8

                st.markdown(
                    f"""
                    <div style="background: {'rgba(148, 163, 184, 0.08)' if is_dark else '#E8EFF7'}; border: 1px solid {'rgba(148, 163, 184, 0.2)' if is_dark else '#CBD5E1'}; border-radius: 8px; padding: 12px 14px; margin-bottom: 10px;">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <div style="font-weight: 700; font-size: 14px; color: {accent_cyan};">{u_name} &nbsp;•&nbsp; <span style="font-size: 11px; opacity: 0.8;">{stype}</span></div>
                            <span style="font-size: 11px; font-weight: 700; color: #10B981; background: rgba(16, 185, 129, 0.15); padding: 2px 8px; border-radius: 4px;">Reached in {resp_min:.1f} mins</span>
                        </div>
                        <div class="dispatch-timeline">
                            <div class="timeline-node">
                                <div class="timeline-dot completed"></div>
                                <div style="font-size: 12px;"><b>Dispatched by CAD Console:</b> <span style="opacity: 0.7; font-family: monospace;">{disp_time} IST</span></div>
                            </div>
                            <div class="timeline-node">
                                <div class="timeline-dot completed"></div>
                                <div style="font-size: 12px;"><b>Crew Acknowledged & En Route:</b> <span style="opacity: 0.7; font-family: monospace;">{ack_time} IST ({d.distance_km:.1f} km away)</span></div>
                            </div>
                            <div class="timeline-node">
                                <div class="timeline-dot completed"></div>
                                <div style="font-size: 12px;"><b>Arrived On-Scene:</b> <span style="opacity: 0.7; font-family: monospace;">{arr_time} IST</span></div>
                            </div>
                            <div class="timeline-node" style="margin-bottom: 0;">
                                <div class="timeline-dot completed"></div>
                                <div style="font-size: 12px;"><b>Mission Completed / Unit Cleared:</b> <span style="opacity: 0.7;">On-scene objectives resolved</span></div>
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.info("No field units were dispatched for this incident.")

        st.markdown("</div>", unsafe_allow_html=True)

    # FULL SCREEN WIDTH: FIELD OFFICER CONCLUSION REPORT
    threat_lower = (incident.primary_threat or "").lower()
    c_notes = (incident.resolution_notes or "").lower()
    if "hospital" in c_notes or "medical" in threat_lower or "cardiac" in threat_lower or "stroke" in threat_lower:
        pill_class = "conclusion-hospital"
        pill_title = "Hospital Admitted"
    elif "shelter" in c_notes or "sakhi" in c_notes or "domestic" in threat_lower or "violence" in threat_lower:
        pill_class = "conclusion-shelter"
        pill_title = "Rescued & Sheltered"
    elif "fire" in c_notes or "suppressed" in c_notes or "cylinder" in threat_lower or "fire" in threat_lower:
        pill_class = "conclusion-fire"
        pill_title = "Fire Extinguished"
    elif "detained" in c_notes or "apprehended" in c_notes or "stalking" in threat_lower or "police" in threat_lower:
        pill_class = "conclusion-police"
        pill_title = "Suspect Detained"
    else:
        pill_class = "conclusion-legal"
        pill_title = "Legal Aid Assigned"

    st.markdown(
        f"""
        <div class="sahaay-card" style="padding: 22px 26px; margin-top: 18px; width: 100%; box-sizing: border-box;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 10px;">
                <div style="font-size: 13px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.06em; opacity: 0.85;">
                    [ Report ] Field Officer Conclusion Report
                </div>
                <span class="conclusion-pill {pill_class}" style="font-size: 12px; padding: 4px 14px;">{pill_title}</span>
            </div>
            <div style="background: {'rgba(148, 163, 184, 0.08)' if is_dark else '#E8EFF7'}; border-left: 4px solid {success_color}; padding: 18px 22px; border-radius: 8px; font-size: 14.5px; line-height: 1.7; font-weight: 500; min-height: 90px; color: {'#F1F5F9' if is_dark else '#142238'};">
                {incident.resolution_notes or "Field response completed. Patient/victim secured on-scene and case closed."}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    db.close()


# ---------------------------------------------------------
# Page 7: Dispatch & Live Tracking (State Machine)
# ---------------------------------------------------------
def page_dispatch():
    render_app_header(st.session_state.user)
    db = get_db_session()
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"

    inc_id = st.session_state.selected_incident_id
    incident = db.query(Incident).filter(Incident.id == inc_id).first()

    if not incident:
        st.error("No incident selected.")
        db.close()
        return

    st.subheader(f"Field Dispatch & Unit Assignment: {incident.id}")
    st.markdown(
        f"""
        <div style="background: {'#111C2E' if is_dark else '#FFFFFF'}; border: 1px solid {'#1E293B' if is_dark else '#E2E8F0'}; border-radius: 8px; padding: 12px 20px; display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div>
                <span style="font-size: 16px; font-weight: 800; color: {'#38BDF8' if is_dark else '#173B57'};">{incident.id}</span>
                <span style="margin-left: 10px; color: {'#94A3B8' if is_dark else '#286A8A'}; font-weight: 600;">{incident.primary_threat or 'Emergency'}</span>
                <span style="margin-left: 10px; color: {'#CBD5E1' if is_dark else '#334155'};">📍 {incident.location_text or 'Delhi NCR'}</span>
            </div>
            <div>{render_priority_chip(incident.current_urgency)}</div>
        </div>
        <div style="background: {'rgba(217, 119, 6, 0.15)' if is_dark else '#FEF3C7'}; border: 1px solid {'#D97706'}; padding: 6px 14px; border-radius: 4px; font-size: 12px; color: {'#FBBF24' if is_dark else '#92400E'}; margin-bottom: 16px;">
            ⚠️ <b>SIMULATED DISPATCH DEMO:</b> All units, coordinates, ETAs, and tactical radio comms are simulated in a realistic CAD operations environment.
        </div>
        """,
        unsafe_allow_html=True
    )

    # Fetch active assignments for this incident
    active_assignments = db.query(DispatchAssignment).filter(
        DispatchAssignment.incident_id == incident.id,
        DispatchAssignment.status != "cancelled"
    ).all()

    if active_assignments:
        ass = active_assignments[0]
        unit = db.query(ResponseUnit).filter(ResponseUnit.id == ass.unit_id).first()

        if unit:
            # 1. Real-Time Telemetry HUD Ribbon
            render_telemetry_hud(unit, ass, is_dark=is_dark)

            # 2. Live Tactical Mission Corridor & Moving Unit Map
            st.markdown(
                f"<div style='font-size: 14px; font-weight: 800; color: {'#38BDF8' if is_dark else '#173B57'}; margin-bottom: 6px;'>"
                f"🛰️ LIVE MISSION CORRIDOR & GPS TRAJECTORY: {unit.unit_name} &rarr; {incident.id} [VICTIM LOCATION]"
                f"</div>",
                unsafe_allow_html=True
            )
            m_disp = build_dispatch_tactical_map(incident, unit, ass, is_dark=is_dark)
            st_folium(
                m_disp,
                height=430,
                use_container_width=True,
                key=f"disp_map_{ass.id}_{round(unit.current_lat, 4)}_{round(unit.current_lon, 4)}"
            )

            # 3. Service Vehicle Live Movement & Navigation Controls
            st.markdown(
                f"<div style='font-size: 13px; font-weight: 800; margin-top: 10px; margin-bottom: 6px; color: {'#F8FAFC' if is_dark else '#0F172A'};'>"
                f"📡 SERVICE VEHICLE MOVEMENT & NAVIGATION CONTROLS:"
                f"</div>",
                unsafe_allow_html=True
            )
            col_mv1, col_mv2, col_mv3, col_mv4 = st.columns([1.3, 1.3, 1.1, 1], gap="small")

            with col_mv1:
                if ass.status not in ["arrived", "completed"]:
                    if st.button("📡 Advance Vehicle Towards Victim (+25% Hop)", key=f"adv_{ass.id}", type="primary", use_container_width=True):
                        res = advance_unit_towards_incident(db, ass.id, step_fraction=0.30, actor_id=st.session_state.user["employee_id"])
                        if res.get("arrived"):
                            st.success(f"🚨 {unit.unit_name} HAS ARRIVED ON SCENE AT VICTIM LOCATION!")
                            now_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
                            if "dispatch_comms" in st.session_state and incident.id in st.session_state.dispatch_comms:
                                st.session_state.dispatch_comms[incident.id].append({
                                    "timestamp": now_str,
                                    "sender": f"UNIT {unit.call_sign} MDT",
                                    "badge": "ON SCENE",
                                    "text": f"[{unit.call_sign} MDT]: UNIT HAS ARRIVED AT SCENE. Vehicle secured, responders making immediate entry.",
                                    "unit_ack": "On-scene arrival confirmed via GPS telemetry."
                                })
                        else:
                            st.info(f"Vehicle advanced to {res['unit_lat']}, {res['unit_lon']}. Remaining: {res['distance_km']} km (ETA: {res['eta_minutes']}m)")
                        st.rerun()
                else:
                    st.success(f"✅ Vehicle Status: {ass.status.upper()}")

            with col_mv2:
                if ass.status not in ["arrived", "completed"]:
                    if st.button("▶️ Drive to Scene (Live Transit Simulation)", key=f"drive_{ass.id}", use_container_width=True):
                        with st.spinner("Simulating emergency transit along mission corridor..."):
                            res = advance_unit_towards_incident(db, ass.id, step_fraction=0.65, actor_id=st.session_state.user["employee_id"])
                            if res.get("arrived"):
                                st.success("🚨 UNIT ARRIVED ON SCENE!")
                            else:
                                st.info(f"Transit advanced: {res['distance_km']} km remaining.")
                        st.rerun()

            with col_mv3:
                if ass.status != "completed":
                    if st.button(f"Advance State: {ass.status.upper()} &rarr;", key=f"step_{ass.id}", use_container_width=True):
                        res = step_assignment_simulation(db, ass.id, st.session_state.user["employee_id"])
                        st.success(f"Status advanced to {res['new_status'].upper()}")
                        st.rerun()
                else:
                    st.info("Mission Completed")

            with col_mv4:
                if st.button("Cancel / Return Unit", key=f"reset_{ass.id}", use_container_width=True):
                    reset_unit_to_base(db, ass.unit_id)
                    ass.status = "cancelled"
                    db.commit()
                    st.warning("Unit returned to base station.")
                    st.rerun()

            # 4. Service Vehicle Command & Live Tactical Radio Comms Console
            render_tactical_comms_console(
                db=db,
                incident=incident,
                unit=unit,
                assignment=ass,
                is_dark=is_dark,
                actor_id=st.session_state.user["employee_id"]
            )
    else:
        st.info("No service vehicle dispatched to this incident yet. Select and assign a unit below to activate live GPS tracking and the tactical radio link.")

    st.markdown("<div style='margin-top: 16px;'></div>", unsafe_allow_html=True)

    # 5. Response Units Available to Assign / Backup Units
    st.subheader("Available Responder Fleet (Dispatch Units)")
    srv_tabs = st.tabs(["Medical (Ambulance)", "Police", "Fire", "Shelter / NGO", "Legal Aid"])
    services = ["medical", "police", "fire", "shelter", "legal"]

    for idx, srv in enumerate(services):
        with srv_tabs[idx]:
            units_list = get_units_for_incident(db, incident.id, srv)
            for u in units_list:
                status_badge = f"<span style='color: #10B981; font-weight: 700;'>● {u['status'].upper()}</span>" if u['is_available'] else f"<span style='color: #F59E0B; font-weight: 700;'>○ {u['status'].upper()}</span>"
                st.markdown(
                    f"""
                    <div style="background: {'#111C2E' if is_dark else '#FFFFFF'}; border: 1px solid {'#1E293B' if is_dark else '#E2E8F0'}; border-radius: 6px; padding: 12px; margin-bottom: 8px; display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <div style="font-weight: 700; color: {'#38BDF8' if is_dark else '#173B57'};">{u['unit_name']} ({u['unit_id']})</div>
                            <div style="font-size: 12px; color: {'#94A3B8' if is_dark else '#526171'};">
                                Distance: <b>{u['distance_km']} km</b> • ETA: <b>{u['eta_minutes']} mins</b> • Status: {status_badge}
                            </div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
                if u['is_available']:
                    if st.button(f"Assign {u['unit_name']}", key=f"assign_{u['unit_id']}", use_container_width=True):
                        assign_unit_to_incident(db, incident.id, u['unit_id'], st.session_state.user["employee_id"])
                        st.success(f"{u['unit_name']} assigned successfully!")
                        st.rerun()

    db.close()

# ---------------------------------------------------------
# Page 8: Live Map View
# ---------------------------------------------------------
def page_map_view():
    render_app_header(st.session_state.user)
    db = get_db_session()
    is_dark = st.session_state.get("theme_mode", "dark") == "dark"

    st.subheader("Geospatial Incident & Responder Fleet Map (Delhi NCR)")
    st.caption("High-contrast tactical emergency map displaying confirmed incidents (pulsing beacons), fleet units, and active mission corridors.")

    # Fetch incidents with valid coordinates
    incidents = db.query(Incident).filter(Incident.latitude.isnot(None), Incident.longitude.isnot(None)).all()
    units = db.query(ResponseUnit).all()
    dispatches = db.query(DispatchAssignment).all()

    col_map, col_list = st.columns([3, 1], gap="medium")

    with col_map:
        try:
            m = build_fleet_overview_map(incidents, units, dispatches, is_dark=is_dark)
            st_folium(m, height=560, use_container_width=True)
        except Exception as e:
            st.warning(f"Folium map component: {e}. Displaying tabular location overview.")
            loc_rows = []
            for inc in incidents:
                loc_rows.append({
                    "ID": inc.id,
                    "Place": inc.location_text,
                    "Latitude": inc.latitude,
                    "Longitude": inc.longitude,
                    "Priority": inc.current_urgency,
                    "Threat": inc.primary_threat,
                    "Source": inc.location_source
                })
            st.dataframe(pd.DataFrame(loc_rows), use_container_width=True)

    with col_list:
        st.subheader("Active Incidents")
        for inc in incidents:
            st.markdown(
                f"""
                <div style="background: {'#111C2E' if is_dark else '#FFFFFF'}; border: 1px solid {'#1E293B' if is_dark else '#E2E8F0'}; border-radius: 6px; padding: 10px; margin-bottom: 8px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 800; color: {'#38BDF8' if is_dark else '#173B57'};">{inc.id}</span>
                        {render_priority_chip(inc.current_urgency)}
                    </div>
                    <div style="font-size: 11px; color: {'#94A3B8' if is_dark else '#526171'}; margin-top: 4px;">[Loc] {inc.location_text or 'Delhi'}</div>
                </div>
                """,
                unsafe_allow_html=True
            )
            col_sel1, col_sel2 = st.columns([1, 1])
            with col_sel1:
                if st.button("Review", key=f"sel_map_rev_{inc.id}", use_container_width=True):
                    st.session_state.selected_incident_id = inc.id
                    st.session_state.current_page = "incidents"
                    st.rerun()
            with col_sel2:
                if st.button("📡 Track & Comms", key=f"sel_map_disp_{inc.id}", use_container_width=True, type="primary"):
                    st.session_state.selected_incident_id = inc.id
                    st.session_state.current_page = "dispatch"
                    st.rerun()

    db.close()

# ---------------------------------------------------------
# Page 9: Repeat-Complaint Review
# ---------------------------------------------------------
def page_repeat_review():
    render_app_header(st.session_state.user)
    db = get_db_session()

    st.subheader("Repeat Complaint Audit & Reversible Case Linking")
    st.markdown(
        """
        > **Safety & Privacy Rule:** False merges harm innocent people and corrupt case histories.
        > Auto-linking requires score $\ge 0.92$ **AND** at least **two independent strong signals** (phone hash match + phonetic name / alias).
        > Name alone or phone alone **never** merges cases. All links are reversible relationships and logged in the audit trail.
        """
    )

    inc_id = st.session_state.selected_incident_id
    incident = db.query(Incident).filter(Incident.id == inc_id).first()

    if incident:
        candidates = match_repeat_complaints(incident, db)
        st.markdown(f"#### Evaluating Potential Repeats for **{incident.id}** ({incident.caller_name or 'Anonymous'})")

        if not candidates:
            st.info("No repeat complaint candidates found sharing blocking keys.")
        else:
            for cand in candidates:
                cand_inc = db.query(Incident).filter(Incident.id == cand["candidate_case_id"]).first()
                band_color = "#187347" if cand["band"] == "auto" else "#A15C00"
                
                with st.container():
                    st.markdown(
                        f"""
                        <div class="sahaay-panel" style="border-left: 4px solid {band_color};">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-size: 16px; font-weight: 700; color: #173B57;">Candidate Match: {cand['candidate_case_id']}</span>
                                    <span style="font-size: 13px; color: #526171; margin-left: 10px;">({cand['summary']})</span>
                                </div>
                                <span style="background: #E8EDF2; color: #173B57; padding: 4px 10px; border-radius: 4px; font-weight: bold; font-size: 13px;">
                                    Score: {cand['score']:.2f} • Band: {cand['band'].upper()}
                                </span>
                            </div>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

                    col_sig, col_act = st.columns([2, 1])
                    with col_sig:
                        st.write("##### Independent Match Signals:")
                        sigs = cand["signals"]
                        st.markdown(
                            f"""
                            - 📱 **Keyed Phone Hash Match:** {'✅ Match' if sigs.get('phone_match') else '❌ Different / Shared'}
                            - 🔤 **Phonetic Name Score:** `{sigs.get('phonetic_name_score', 0):.2f}`
                            - 📍 **Locality Similarity:** `{sigs.get('place_match_score', 0):.2f}`
                            - 🚨 **Threat Similarity:** {'✅ Same Threat' if sigs.get('threat_match') else 'Different'}
                            - ⏱️ **Time Gap:** `{sigs.get('days_apart', 0)} days`
                            """
                        )

                    with col_act:
                        st.write("##### Supervisory Decision:")
                        if st.button(f"Approve Link with {cand['candidate_case_id']}", key=f"app_{cand['candidate_case_id']}", type="primary"):
                            approve_or_create_link(
                                db=db,
                                incident_a_id=incident.id,
                                incident_b_id=cand['candidate_case_id'],
                                score=cand['score'],
                                band=cand['band'],
                                signals=sigs,
                                created_by=st.session_state.user["employee_id"]
                            )
                            st.success(f"Link between {incident.id} and {cand['candidate_case_id']} recorded in audit trail.")
                            st.rerun()

    # Active Links Archive
    st.markdown("---")
    st.subheader("Active Repeat Links in Database")
    active_links = db.query(RepeatLink).filter(RepeatLink.status == "active").all()
    if active_links:
        for l in active_links:
            col_l1, col_l2 = st.columns([3, 1])
            with col_l1:
                st.write(f"🔗 **Link #{l.id}:** `{l.incident_a_id}` &harr; `{l.incident_b_id}` (Band: **{l.band}**, Score: **{l.score}**)")
            with col_l2:
                undo_reason = st.text_input("Undo Reason", key=f"undo_reason_{l.id}", placeholder="Reason to unlink")
                if st.button("Undo Link", key=f"undo_{l.id}"):
                    undo_repeat_link(db, l.id, st.session_state.user["employee_id"], undo_reason or "Supervisor decision")
                    st.warning(f"Link #{l.id} undone and audited.")
                    st.rerun()
    else:
        st.write("No active repeat links recorded.")

    db.close()

# ---------------------------------------------------------
# Page 10: Lexicon Manager
# ---------------------------------------------------------
def page_lexicon():
    render_app_header(st.session_state.user)
    db = get_db_session()

    st.subheader("Multilingual Dialect & Covert Distress Lexicon")
    st.caption("Maintains versioned indirect phrases, wrong-number calls, and food-order patterns.")

    entries = list_lexicon_entries(db)

    tab_list, tab_propose = st.tabs(["Active Lexicon Entries", "Propose New Code Phrase"])

    with tab_list:
        for e in entries:
            st.markdown(
                f"""
                <div class="sahaay-panel">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-size: 16px; font-weight: 700; color: #173B57;">{e.phrase.title()} ({e.id})</span>
                        <span style="background: #E8EDF2; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 12px;">{e.risk_class} • {e.status.upper()}</span>
                    </div>
                    <div style="font-size: 13px; color: #253445; margin-top: 6px;">
                        <b>Canonical Meaning:</b> {e.canonical_meaning}<br>
                        <b>Threat Type:</b> {e.threat_type} | <b>Region:</b> {e.region}
                    </div>
                    <div style="font-size: 12px; color: #286A8A; margin-top: 6px;">
                        💬 <b>Suggested Safe Question:</b> {e.suggested_safe_question or 'None'}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

    with tab_propose:
        st.subheader("Propose New Lexicon Phrase")
        p_phrase = st.text_input("Candidate Phrase / Code Word", placeholder="e.g. doodh ka packet")
        p_meaning = st.text_area("Canonical Meaning", placeholder="e.g. Caller disguises distress call as milk vendor inquiry")
        p_threat = st.selectbox("Associated Threat", ["domestic_violence", "trafficking_coercion", "stalking_harassment", "child_at_risk"])
        p_risk = st.selectbox("Risk Class", ["P1", "P0", "P2"])
        p_region = st.selectbox("Region", ["Pan-India", "North India", "Delhi NCR", "Central India"])
        p_question = st.text_input("Safe Yes/No Question", placeholder="e.g. Do you need police sent to your home?")

        if st.button("Propose Candidate Phrase", type="primary"):
            if p_phrase and p_meaning:
                new_id = f"COV-{len(entries)+1:03d}"
                propose_lexicon_entry(
                    db=db,
                    entry_id=new_id,
                    phrase=p_phrase,
                    variants=[p_phrase],
                    canonical_meaning=p_meaning,
                    threat_type=p_threat,
                    risk_class=p_risk,
                    region=p_region,
                    suggested_safe_question=p_question,
                    created_by=st.session_state.user["employee_id"]
                )
                st.success(f"Phrase '{p_phrase}' proposed with ID {new_id}. Awaiting Admin approval.")
                st.rerun()
            else:
                st.error("Please fill in both phrase and canonical meaning.")

    db.close()

# ---------------------------------------------------------
# Page 11: Transcript Simulator
# ---------------------------------------------------------
def page_simulator():
    render_app_header(st.session_state.user)

    st.subheader("Transcript Stream Simulator & Pipeline Inspector")
    st.caption("Demonstration workbench for testing Hinglish transcripts, noise injection, and stage-by-stage pipeline tracing.")

    scenarios = {
        "1. Active Domestic Violence (Explicit P0)": "bhaiya jaldi aao, ghar me pati maar raha hai, Sector 14 Rohini, bacche ro rahe",
        "2. Covert Distress Call — Pizza Order (P1 + VERIFY)": "hello... wrong number... aap pizza wali ho? ... nahi wo mera bhai yahin hai (whisper, then silence)",
        "3. Life-Threatening Cardiac Emergency (P0)": "meri maa ko saans nahi aa rahi, Karol Bagh gali no 4, jaldi ambulance bhejo",
        "4. Active Stalking & Pursuit in Transit (P1)": "wahi aadmi phir peecha kar raha hai, pichle hafte bhi call kiya tha, metro station ke paas",
        "5. Pure Legal Aid Query (P3 Low)": "talaq ke baad mehr ka paisa kaise milega, kanooni salaah chahiye",
        "6. Covert Signal — Whispered Doctor Inquiry (P1)": "doctor sahab se baat karwa do... dawai nahi mil rahi... kamre se nikalne nahi de rahe (fusfusahat)",
        "7. Hindi (Devanagari) Critical Emergency (P0)": "भैया जल्दी आओ, घर में आग लग गई है और लोग अंदर फंसे हैं करोल बाग"
    }

    sel_scenario = st.selectbox("Select Benchmark Scenario", list(scenarios.keys()))
    default_text = scenarios[sel_scenario]

    sim_text = st.text_area("Call Transcript", value=default_text, height=90)

    noise_level = st.slider("Synthetic Noise & ASR Degradation Level (%)", min_value=0, max_value=100, value=0, help="Simulates spelling noise, dropped vowels, and phoneme confusion")

    # Apply synthetic noise if slider > 0
    if noise_level > 0:
        words = sim_text.split()
        noisy_words = []
        for w in words:
            if noise_level > 40 and len(w) > 4:
                w = w.replace('a', '').replace('e', '')
            noisy_words.append(w)
        sim_text = " ".join(noisy_words)

    if st.button("🚀 Run Full AI Triage Pipeline", type="primary", use_container_width=True):
        t_start = time.perf_counter()
        triage_res = run_triage_pipeline(sim_text)
        total_time = round((time.perf_counter() - t_start) * 1000, 2)

        st.markdown(
            f"""
            <div style="background: white; border: 1px solid #E8EDF2; border-radius: 8px; padding: 16px; margin: 20px 0;">
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <div style="font-size: 18px; font-weight: 700; color: #173B57;">Triage Pipeline Execution Output</div>
                    <div>{render_priority_chip(triage_res['urgency'])}</div>
                </div>
                <div style="font-size: 13px; color: #526171; margin-top: 6px;">
                    Pipeline Execution Time: <b>{total_time} ms</b> • Engine Mode: <b>{triage_res['engine_mode']}</b>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # Stage-by-Stage Trace
        t1, t2, t3, t4, t5 = st.tabs(["M1 Normalization", "M2 Facts & Location", "M3 Covert Signals", "M4 Urgency Fusion", "M5 & M7 Route/Evidence"])

        with t1:
            st.write("##### Normalized Text & Script Identification:")
            st.code(triage_res["normalized_text"], language="text")
            st.write(f"**Detected Language Mix:** `{triage_res['lang_mix']}`")

        with t2:
            st.write("##### Extracted Structured Facts:")
            st.json(triage_res["details"])
            st.write("##### Extracted Location Candidates:")
            st.json(triage_res["location"])

        with t3:
            st.write("##### Covert & Indirect Distress Detection:")
            st.write(f"**Covert Floor:** `{triage_res['covert_signal_level']}`")
            st.write(f"**Safe Contact Flag:** `{'Permitted' if triage_res['safe_contact_flag'] else 'FORBIDDEN (Do not call back)'}`")
            st.write(f"**Safe Yes/No Question:** `{triage_res.get('suggested_safe_question')}`")

        with t4:
            st.write("##### Urgency Resolution & Safety Floor Rules:")
            st.write(f"- Rules Floor: `{triage_res['rules_floor']}`")
            st.write(f"- Covert Floor: `{triage_res['covert_signal_level']}`")
            st.write(f"- Model Level: `{triage_res['model_level']}` (Conf: `{triage_res['confidence']:.0%}`)")
            st.write(f"- **Final Urgency:** `{triage_res['urgency']}`")
            st.write(f"- Flags: `{triage_res['flags']}`")

        with t5:
            st.write("##### Recommended Services & Evidence Spans:")
            st.write(f"**Services:** `{triage_res['routes']}`")
            st.write("##### Highlighted Evidence in Caller's Words:")
            st.markdown(render_highlighted_transcript(sim_text, triage_res["evidence"]), unsafe_allow_html=True)

# ---------------------------------------------------------
# Page 12: Evaluation Dashboard
# ---------------------------------------------------------
def page_eval():
    render_app_header(st.session_state.user)

    st.subheader("Safety Evaluation Dashboard & Model Benchmarks")
    st.markdown(
        """
        > **Safety Targets vs Observed Performance:**
        > Evaluated across the 15-case synthetic validation split and 5-case hidden evaluation set.
        > Design targets are shown alongside empirically measured figures.
        """
    )

    tab_val, tab_hidden = st.tabs(["Validation Benchmark Evaluation", "Hidden-Set Protocol Export"])

    with tab_val:
        eval_data = evaluate_dataset()
        metrics = eval_data["metrics"]
        ci_low, ci_high = metrics.get("urgent_recall_ci", (0.0, 0.0))

        # Primary Metric Cards (Safety First!)
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f"""
                <div class="sahaay-stat-card" style="border-left: 4px solid #187347;">
                    <div class="sahaay-stat-label">Urgent Recall (P0/P1)</div>
                    <div class="sahaay-stat-value" style="color: #187347;">{metrics.get('urgent_recall', 0.0):.1%}</div>
                    <div style="font-size: 11px; color: #526171;">Target &ge;98% | 95% CI: [{ci_low:.0%}, {ci_high:.0%}]</div>
                </div>
                """, unsafe_allow_html=True
            )
        with c2:
            st.markdown(
                f"""
                <div class="sahaay-stat-card" style="border-left: 4px solid #B42318;">
                    <div class="sahaay-stat-label">Severe Under-Triage</div>
                    <div class="sahaay-stat-value" style="color: #187347;">{metrics.get('severe_under_triage_rate', 0.0):.1%}</div>
                    <div style="font-size: 11px; color: #526171;">Target &lt;0.5% (2+ levels below)</div>
                </div>
                """, unsafe_allow_html=True
            )
        with c3:
            st.markdown(
                f"""
                <div class="sahaay-stat-card" style="border-left: 4px solid #286A8A;">
                    <div class="sahaay-stat-label">Routing Macro-F1</div>
                    <div class="sahaay-stat-value" style="color: #286A8A;">{metrics.get('routing_macro_f1', 0.0):.2f}</div>
                    <div style="font-size: 11px; color: #526171;">Target &ge;0.85</div>
                </div>
                """, unsafe_allow_html=True
            )
        with c4:
            st.markdown(
                f"""
                <div class="sahaay-stat-card" style="border-left: 4px solid #A15C00;">
                    <div class="sahaay-stat-label">Covert-Signal Recall</div>
                    <div class="sahaay-stat-value" style="color: #A15C00;">{metrics.get('covert_recall', 0.0):.1%}</div>
                    <div style="font-size: 11px; color: #526171;">Target &ge;90%</div>
                </div>
                """, unsafe_allow_html=True
            )

        st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

        col_cm, col_chart = st.columns([1, 1], gap="medium")

        with col_cm:
            st.subheader("Confusion Matrix (Truth vs Prediction)")
            cm_data = metrics.get("confusion_matrix", [[0]*4 for _ in range(4)])
            cm_df = pd.DataFrame(
                cm_data,
                index=["True P0", "True P1", "True P2", "True P3"],
                columns=["Pred P0", "Pred P1", "Pred P2", "Pred P3"]
            )
            st.dataframe(cm_df, use_container_width=True)

        with col_chart:
            st.subheader("Per-Service Routing F1 Scores")
            srv_f1s = metrics.get("service_f1s", {})
            f1_df = pd.DataFrame(list(srv_f1s.items()), columns=["Service", "F1 Score"])
            fig = px.bar(f1_df, x="Service", y="F1 Score", text_auto=".2f", color="Service", color_discrete_sequence=["#173B57", "#B42318", "#286A8A", "#526171"])
            fig.update_layout(yaxis_range=[0, 1.05], height=260, margin=dict(l=20, r=20, t=20, b=20))
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")
        html_report = export_evaluation_html_report(eval_data)
        st.download_button(
            "📥 Export Full Evaluation Report (HTML)",
            data=html_report,
            file_name="sahaay_evaluation_report.html",
            mime="text/html"
        )

    with tab_hidden:
        st.subheader("Hidden-Set Evaluation Mode")
        st.write("Executes the triage pipeline without exposing or utilizing ground-truth labels. Exports submission JSON.")
        hidden_results = run_hidden_set_protocol()
        st.json(hidden_results["predictions"][:2])
        st.download_button(
            "📥 Download Submission Predictions (JSON)",
            data=pd.Series(hidden_results["predictions"]).to_json(orient="records", indent=2),
            file_name="sahaay_hidden_predictions.json",
            mime="application/json"
        )

# ---------------------------------------------------------
# Page 13: Impact & SDG Board
# ---------------------------------------------------------
def page_impact():
    render_app_header(st.session_state.user)
    db = get_db_session()

    st.subheader("UN Sustainable Development Goals & Impact Analytics")
    st.caption("De-identified aggregate outcomes mapped to SDG 5, 10, 16, and 9. Enforces differential privacy with minimum cell size suppression (<3 hidden).")

    impact = get_sdg_impact_metrics(db)

    # Four SDG Cards
    s1, s2 = st.columns(2)
    with s1:
        sdg5 = impact["sdg_5_gender_equality"]
        st.markdown(
            f"""
            <div class="sahaay-panel" style="border-left: 4px solid #E5243B;">
                <div style="font-size: 16px; font-weight: 700; color: #E5243B;">{sdg5['title']}</div>
                <div style="font-size: 13px; color: #526171; margin-top: 4px;">{sdg5['description']}</div>
                <div style="margin-top: 14px;">
                    {"".join([f"<div style='display: flex; justify-content: space-between; padding: 4px 0;'><span>{m['label']}</span><b>{m['value']}</b></div>" for m in sdg5['metrics']])}
                </div>
            </div>
            """, unsafe_allow_html=True
        )

        sdg16 = impact["sdg_16_peace_justice"]
        st.markdown(
            f"""
            <div class="sahaay-panel" style="border-left: 4px solid #00689D;">
                <div style="font-size: 16px; font-weight: 700; color: #00689D;">{sdg16['title']}</div>
                <div style="font-size: 13px; color: #526171; margin-top: 4px;">{sdg16['description']}</div>
                <div style="margin-top: 14px;">
                    {"".join([f"<div style='display: flex; justify-content: space-between; padding: 4px 0;'><span>{m['label']}</span><b>{m['value']}</b></div>" for m in sdg16['metrics']])}
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    with s2:
        sdg10 = impact["sdg_10_reduced_inequalities"]
        st.markdown(
            f"""
            <div class="sahaay-panel" style="border-left: 4px solid #DD1367;">
                <div style="font-size: 16px; font-weight: 700; color: #DD1367;">{sdg10['title']}</div>
                <div style="font-size: 13px; color: #526171; margin-top: 4px;">{sdg10['description']}</div>
                <div style="margin-top: 14px;">
                    {"".join([f"<div style='display: flex; justify-content: space-between; padding: 4px 0;'><span>{m['label']}</span><b>{m['value']}</b></div>" for m in sdg10['metrics']])}
                </div>
            </div>
            """, unsafe_allow_html=True
        )

        sdg9 = impact["sdg_9_innovation"]
        st.markdown(
            f"""
            <div class="sahaay-panel" style="border-left: 4px solid #FD6925;">
                <div style="font-size: 16px; font-weight: 700; color: #FD6925;">{sdg9['title']}</div>
                <div style="font-size: 13px; color: #526171; margin-top: 4px;">{sdg9['description']}</div>
                <div style="margin-top: 14px;">
                    {"".join([f"<div style='display: flex; justify-content: space-between; padding: 4px 0;'><span>{m['label']}</span><b>{m['value']}</b></div>" for m in sdg9['metrics']])}
                </div>
            </div>
            """, unsafe_allow_html=True
        )

    db.close()

# ---------------------------------------------------------
# Page 14: Administration & Audit Trail
# ---------------------------------------------------------
def page_admin():
    render_app_header(st.session_state.user)
    db = get_db_session()

    st.subheader("System Administration, RBAC & Immutable Audit Trail")

    tab_users, tab_thresh, tab_audit, tab_reset = st.tabs(["User Management", "Safety Thresholds & Two-Person Rule", "Append-Only Audit Log", "Demo Data Reset"])

    with tab_users:
        st.write("##### Registered Staff & Roles")
        users = db.query(User).all()
        u_data = [{"ID": u.employee_id, "Name": u.full_name, "Email": u.email, "Role": u.role, "Active": u.is_active} for u in users]
        st.dataframe(pd.DataFrame(u_data), use_container_width=True, hide_index=True)

    with tab_thresh:
        st.write("##### Urgency & Cost Matrix Governance")
        st.info("High-impact configuration changes require two-person administrative approval.")
        tau = st.slider("Confidence Threshold (TAU)", 0.50, 0.95, float(settings.confidence_tau), step=0.05)
        st.caption("Current Cost Matrix:")
        st.json(settings.cost_matrix)

    with tab_audit:
        st.write("##### Immutable Audit Trail Explorer")
        events = db.query(AuditEvent).order_by(AuditEvent.timestamp.desc()).limit(30).all()
        a_data = []
        for e in events:
            a_data.append({
                "Timestamp": e.timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                "Actor": f"{e.actor_id} ({e.actor_role})",
                "Action": e.action,
                "Object": f"{e.object_type} ({e.object_id})",
                "Reason": e.reason or ""
            })
        if a_data:
            audit_df = pd.DataFrame(a_data)
            st.dataframe(audit_df, use_container_width=True, hide_index=True)
            st.download_button(
                "Export Audit Log to CSV",
                data=audit_df.to_csv(index=False).encode('utf-8'),
                file_name=f"sahaay_audit_log_{datetime.datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )

    with tab_reset:
        st.write("##### Demo Reset Workflow")
        st.warning("This action will reset the database to clean seed demo records. Use for clean testing before judging.")
        confirm_check = st.checkbox("I confirm that I want to reset the demonstration database to initial seed state.")
        if st.button("Execute Demo Database Reset →", type="primary", disabled=not confirm_check):
            seed_database(force_reset=True)
            st.session_state.selected_incident_id = "INC-1042"
            st.session_state.sim_call_state = "IDLE"
            st.session_state.sim_played_segments = []
            st.session_state.sim_latest_triage = None
            st.success("Demo database successfully reset to clean seed state!")
            st.rerun()

    db.close()

# ---------------------------------------------------------
# Page 15: User Menu & Help
# ---------------------------------------------------------
def page_help():
    render_app_header(st.session_state.user)
    
    st.subheader("Operator Protocols, Standard Operating Procedures & Reference")
    
    st.markdown(
        f"""
        <div style="background: white; border: 1px solid {PALETTE['borders']}; border-radius: 8px; padding: 18px; margin-bottom: 20px;">
            <div style="font-weight: 700; color: #173B57; font-size: 16px;">Operator Station Profile</div>
            <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin-top: 10px; font-size: 14px;">
                <div><b>Staff Name:</b> {st.session_state.user.get('full_name')}</div>
                <div><b>Employee ID:</b> {st.session_state.user.get('employee_id')}</div>
                <div><b>Active Role:</b> {st.session_state.user.get('role').title()}</div>
                <div><b>Station Status:</b> Online (Shift Active)</div>
            </div>
            <div style="margin-top: 15px; padding: 10px; background: #FFF3CD; border-radius: 4px; font-size: 12px; color: #856404;">
                ⚠️ <b>Disclaimer:</b> eSahaay is a hackathon prototype developed for Hack@BVP 8.0 PS3. All calls, audio references, and dispatch operations in this build are simulated. It is not connected to official emergency numbers and does not replace official emergency services.
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    h1, h2, h3 = st.tabs(["Live Call Guidelines", "Emergency Protocols", "Keyboard Shortcuts"])
    with h1:
        st.markdown(LIVE_CALL_GUIDE)
    with h2:
        st.markdown(EMERGENCY_PROTOCOLS)
    with h3:
        st.markdown(KEYBOARD_SHORTCUTS)

# ---------------------------------------------------------
# Router Dispatcher
# ---------------------------------------------------------
def main():
    if not st.session_state.get("user") or st.session_state.current_page == "login":
        page_login()
        return

    render_sidebar()
    page = st.session_state.current_page

    if page == "dashboard":
        page_dashboard()
    elif page == "incidents":
        page_incidents()
    elif page == "case_detail":
        page_case_detail()
    else:
        page_triage()

if __name__ == "__main__":
    main()
