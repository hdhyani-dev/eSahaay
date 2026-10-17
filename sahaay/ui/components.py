"""Reusable UI components for eSahaay Emergency CAD & Triage Console.
Enterprise design standard: Motorola CommandCentral / RapidSOS.
Modern CAD terminal components with official eSahaay branding.
"""
import base64
import os
import re
import streamlit as st
from typing import Dict, Any, List, Optional
from sahaay.ui.theme import PALETTE

def safe_html(html_str: str):
    """
    Render HTML safely in Streamlit without CommonMark markdown parser
    accidentally converting 4-space indented lines into code blocks.
    """
    if hasattr(st, "html"):
        st.html(html_str)
    else:
        cleaned = re.sub(r'\s+', ' ', html_str).strip()
        st.markdown(cleaned, unsafe_allow_html=True)

from pathlib import Path

_ASSETS_DIR = Path(__file__).resolve().parent.parent.parent / "assets"
_LOGO_CACHE: Dict[str, str] = {}

def get_logo_data_uri(kind: str = "full") -> str:
    """Return base64 data URI of the official eSahaay logo or emblem."""
    if kind in _LOGO_CACHE:
        return _LOGO_CACHE[kind]
    target_file = "sahaay_logo_active.png" if kind == "full" else "sahaay_emblem_active.png"
    p = _ASSETS_DIR / target_file
    if p.exists():
        with open(p, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
            _LOGO_CACHE[kind] = f"data:image/png;base64,{encoded}"
            return _LOGO_CACHE[kind]
    return ""

def get_logo_html(width: int = 210) -> str:
    """Generate HTML image tag for full eSahaay logo."""
    uri = get_logo_data_uri("full")
    return f'<img src="{uri}" style="width: {width}px; max-width: 100%; height: auto; object-fit: contain;" alt="eSahaay Logo" />'

def get_emblem_html(width: int = 34) -> str:
    """Generate HTML image tag for compact eSahaay emblem."""
    uri = get_logo_data_uri("emblem")
    return f'<img src="{uri}" style="width: {width}px; max-width: 100%; height: auto; object-fit: contain;" alt="eSahaay" />'

# Compatibility SVG variables (fallback if image not loaded)
LOGO_SVG = get_emblem_html(34)
LOGO_SVG_SIDEBAR = get_emblem_html(32)

def render_app_header(current_user: Optional[Dict[str, Any]] = None):
    """Render top enterprise application bar with official eSahaay branding, telemetry and operator profile."""
    role_name = current_user.get("role", "Operator").title() if current_user else "Operator"
    user_name = current_user.get("full_name", "Operator Staff") if current_user else "Demo Operator"
    emp_id = current_user.get("employee_id", "OP-1042") if current_user else "OP-1042"
    
    parts = user_name.split()
    initials = "".join([p[0].upper() for p in parts[:2]]) if parts else "OP"
    emblem_uri = get_logo_data_uri("emblem")

    theme_mode = st.session_state.get("theme_mode", "dark")
    is_dark = (theme_mode == "dark")
    accent_color = "#22D3EE" if is_dark else "#007F9E"
    sub_color = "#A8B6C9" if is_dark else "#52647B"

    html = f"""
    <div class="sahaay-header">
        <div class="sahaay-brand-title">
            <img src="{emblem_uri}" style="height: 38px; width: auto; object-fit: contain;" alt="eSahaay" />
            <div>
                <div class="sahaay-brand-name">
                    eSAHAAY <span style="font-size: 11px; font-weight: 700; color: {accent_color}; text-transform: uppercase; letter-spacing: 0.08em;">CAD v2.4</span>
                </div>
                <div class="sahaay-tagline">
                    Emergency Response & Multilingual Helpline Triage OS
                </div>
            </div>
        </div>
        <div style="display: flex; align-items: center; gap: 14px;">
            <div class="system-status-capsule">
                <span class="live-pulse-dot"></span>
                <span style="font-weight: 600;">Hybrid AI Active</span>
                <span style="color: {'#64748B' if is_dark else '#94A3B8'};">•</span>
                <span style="color: {accent_color}; font-weight: 700;">Safety Floor: Armed</span>
            </div>
            <div class="operator-profile-pill">
                <div class="operator-avatar">{initials}</div>
                <div>
                    <span style="font-weight: 600;">{user_name}</span>
                    <span style="color: {sub_color}; font-size: 11.5px; margin-left: 6px; font-weight: 600;">({emp_id})</span>
                </div>
            </div>
        </div>
    </div>
    """
    safe_html(html)

def render_priority_chip(urgency: str, is_pinned: bool = False) -> str:
    """Generate sleek enterprise chip for urgency level with clear status dot."""
    urgency = str(urgency).upper()
    pinned_tag = "<span style='font-size:10px; color:#FF5C68; font-weight:700; margin-right:4px;'>PINNED</span>" if is_pinned else ""
    if urgency == "P0":
        return f"<span class='badge-p0'>{pinned_tag}<span class='badge-p0-dot'></span>P0 CRITICAL</span>"
    elif urgency == "P1":
        return "<span class='badge-p1'><span class='badge-p1-dot'></span>P1 HIGH</span>"
    elif urgency == "P2":
        return "<span class='badge-p2'><span class='badge-p2-dot'></span>P2 MEDIUM</span>"
    elif urgency == "P3":
        return "<span class='badge-p3'><span class='badge-p3-dot'></span>P3 LOW</span>"
    elif urgency == "ASSESSING":
        return "<span class='badge-evaluating'><span class='badge-eval-dot'></span>ASSESSING</span>"
    else:
        return "<span class='badge-standby'><span class='badge-standby-dot'></span>AWAITING CALL</span>"

def render_triage_card(triage_data: Dict[str, Any]):
    """
    Render clean, simple Emergency Type & Urgency card.
    Simple titles, direct information, zero explanatory fluff.
    Emergency type only displays after the caller states relevant cues.
    """
    threats = triage_data.get("threat_types", [])
    raw_text = str(triage_data.get("raw_text", "")).strip()
    urgency = triage_data.get("urgency", "PENDING")
    
    # Active threats (excluding 'other' which means no specific emergency stated yet)
    active_threats = [t for t in threats if t.get("type") not in ("other", None)]
    
    if active_threats:
        primary_threat = active_threats[0]["description"]
        chip_html = render_priority_chip(urgency)
    elif raw_text:
        primary_threat = "Awaiting Emergency Details"
        chip_html = render_priority_chip("ASSESSING")
    else:
        primary_threat = "Awaiting Caller Input"
        chip_html = render_priority_chip("PENDING")

    details = triage_data.get("details", {})
    routes = triage_data.get("routes", [])
    locations = triage_data.get("location", [])
    best_loc = locations[0]["text"] if locations else "Pending Caller Input"
    flags = triage_data.get("flags", [])

    theme_mode = st.session_state.get("theme_mode", "dark")
    is_dark = (theme_mode == "dark")
    accent_color = "#22D3EE" if is_dark else "#007F9E"
    warning_color = "#FBBF24" if is_dark else "#956000"
    warning_bg = "rgba(251, 191, 36, 0.15)" if is_dark else "rgba(149, 96, 0, 0.12)"
    warning_border = "rgba(251, 191, 36, 0.4)" if is_dark else "rgba(149, 96, 0, 0.35)"

    verify_html = ""
    if "VERIFY" in flags or triage_data.get("requires_verification"):
        if active_threats:
            verify_html = f"""
            <div style="background: {warning_bg}; border: 1px solid {warning_border}; padding: 8px 12px; margin-bottom: 10px; border-radius: 6px; font-size: 12px; color: {warning_color}; font-weight: 600;">
                ⚠️ <b>Verification Required:</b> Confirm details before dispatching recommended services.
            </div>
            """

    if active_threats and routes:
        service_badges = " ".join([
            f"<span style='background: #0891B2; color: #FFFFFF; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-weight: 700; margin-right: 6px; display: inline-block;'>{s.upper()}</span>"
            for s in routes if s != "no_action"
        ])
    elif raw_text:
        service_badges = "<span style='font-size: 11.5px; opacity: 0.65; font-style: italic;'>Awaiting emergency details from caller...</span>"
    else:
        service_badges = "<span style='font-size: 11.5px; opacity: 0.65; font-style: italic;'>Standby — Call not active</span>"

    if not active_threats and not raw_text:
        status_html = "<b style='color: #64748B;'>Standby</b>"
    elif details.get('ongoing') and active_threats:
        status_html = "<b style='color: #FF5C68;'>Ongoing</b>"
    elif active_threats:
        status_html = "<b style='color: #34D399;'>Stable / Past</b>"
    else:
        status_html = f"<b style='color: {accent_color};'>Assessing</b>"

    html = f"""
    <div class="sahaay-card" style="margin-bottom: 14px; padding: 18px 20px;">
        <div style="font-size: 12px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; opacity: 0.7; margin-bottom: 8px;">
            Emergency Type & Urgency
        </div>
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px;">
            <div style="font-size: 18px; font-weight: 800;">{primary_threat}</div>
            <div>{chip_html}</div>
        </div>
        
        {verify_html}

        <div style="display: grid; grid-template-columns: 1.2fr 1fr 0.8fr; gap: 8px; font-size: 12.5px; margin-bottom: 12px;">
            <div class="telemetry-subcard" style="padding: 8px 10px; border-radius: 6px;">
                <span style="font-size: 10.5px; text-transform: uppercase; font-weight: 600; opacity: 0.7; display: block;">Location</span>
                <b>{best_loc}</b>
            </div>
            <div class="telemetry-subcard" style="padding: 8px 10px; border-radius: 6px;">
                <span style="font-size: 10.5px; text-transform: uppercase; font-weight: 600; opacity: 0.7; display: block;">Weapon / Injury</span>
                <b>{details.get('weapon') or 'None'} / {details.get('injury') or 'None'}</b>
            </div>
            <div class="telemetry-subcard" style="padding: 8px 10px; border-radius: 6px;">
                <span style="font-size: 10.5px; text-transform: uppercase; font-weight: 600; opacity: 0.7; display: block;">Status</span>
                {status_html}
            </div>
        </div>

        <div style="display: flex; align-items: center; gap: 8px;">
            <span style="font-size: 11px; font-weight: 700; opacity: 0.7; text-transform: uppercase;">Recommended Services:</span>
            <div>{service_badges}</div>
        </div>
    </div>
    """
    safe_html(html)

