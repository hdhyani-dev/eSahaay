"""Tactical dispatch map and radio communications engine for eSahaay CAD.
Renders high-contrast, theme-adaptive Folium maps with pulsing victim beacons,
animated response vehicle markers, active mission corridors, and tactical radio comms.
"""
import datetime
from typing import Dict, Any, List, Optional, Tuple
import folium
from folium.plugins import AntPath

# Tile providers
DARK_TILES_URL = "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
LIGHT_TILES_URL = "https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
CARTO_ATTR = '&copy; <a href="https://carto.com/">CARTO</a> &copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

# Service Type Visual Configuration
SERVICE_CONFIG = {
    "police": {
        "label": "Police Patrol",
        "emoji": "🚓",
        "color": "#2563EB",
        "glow": "rgba(37, 99, 235, 0.45)",
        "badge_bg": "#1E40AF"
    },
    "medical": {
        "label": "Ambulance / ALS",
        "emoji": "🚑",
        "color": "#DC2626",
        "glow": "rgba(220, 38, 38, 0.45)",
        "badge_bg": "#991B1B"
    },
    "fire": {
        "label": "Fire & Rescue",
        "emoji": "🚒",
        "color": "#EA580C",
        "glow": "rgba(234, 88, 12, 0.45)",
        "badge_bg": "#C2410C"
    },
    "shelter": {
        "label": "Crisis Van / NGO",
        "emoji": "🛡️",
        "color": "#7C3AED",
        "glow": "rgba(124, 58, 237, 0.45)",
        "badge_bg": "#5B21B6"
    },
    "legal": {
        "label": "Legal Aid / Protection",
        "emoji": "⚖️",
        "color": "#0D9488",
        "glow": "rgba(13, 148, 136, 0.45)",
        "badge_bg": "#0F766E"
    }
}

# Urgency Visual Configuration for Victim Beacons
URGENCY_CONFIG = {
    "P0": {"color": "#DC2626", "pulse_color": "rgba(220, 38, 38, 0.55)", "icon": "🚨", "label": "P0 CRITICAL"},
    "P1": {"color": "#EA580C", "pulse_color": "rgba(234, 88, 12, 0.50)", "icon": "⚠️", "label": "P1 HIGH"},
    "P2": {"color": "#D97706", "pulse_color": "rgba(217, 119, 6, 0.45)", "icon": "⚡", "label": "P2 MEDIUM"},
    "P3": {"color": "#2563EB", "pulse_color": "rgba(37, 99, 235, 0.40)", "icon": "ℹ️", "label": "P3 LOW"},
}

# Tactical Escalation Directives
TACTICAL_PRESET_DIRECTIVES = {
    "CODE_3": {
        "id": "CODE_3",
        "title": "🚨 Code 3 Priority Escalation",
        "directive": "ESCALATION: Upgrade response to Code 3 immediately. Activate dual-tone sirens and emergency strobes. Overtake traffic and expedite transit.",
        "badge": "CODE 3 URGENT",
        "speed_boost": 25.0,
        "sample_ack": "Copy Code 3 upgrade! Sirens and optical warnings engaged. Clearing Outer Ring Rd traffic. ETA revised down."
    },
    "HOSTILE_SCENE": {
        "id": "HOSTILE_SCENE",
        "title": "⚠️ Hostile Threat — Hold Perimeter",
        "directive": "SITUATION ESCALATION: Antagonist reported armed and volatile on premises. DO NOT enter residence alone. Maintain 150m standoff perimeter and await armed backup.",
        "badge": "HOSTILE THREAT",
        "speed_boost": 0.0,
        "sample_ack": "Understood dispatch. Staging unit at outer checkpoint (150m standoff). Visual contact maintained on premise. Standing by for armed support."
    },
    "MEDICAL_ALS": {
        "id": "MEDICAL_ALS",
        "title": "🫀 Medical Trauma — ALS / Defibrillator Ready",
        "directive": "MEDICAL DIRECTIVE: Caller vitals deteriorating, agonal breathing reported. Stage Bag-Valve-Mask, trauma kit, and automated external defibrillator (AED) for immediate breach.",
        "badge": "ALS RESUSCITATION",
        "speed_boost": 15.0,
        "sample_ack": "ALS Paramedic crew briefed. AED charged and trauma crash pack prepped for instant intervention upon arrival."
    },
    "COVERT_ENTRY": {
        "id": "COVERT_ENTRY",
        "title": "🚪 Covert Tactical Approach",
        "directive": "TACTICAL DIRECTIVE: Active domestic dispute. Suspect unaware police called. Cut sirens and flashers 500m prior to location. Approach rear entrance stealthily.",
        "badge": "COVERT APPROACH",
        "speed_boost": -5.0,
        "sample_ack": "Copy silent approach. Sirens cut, running blacked-out stealth beacon. Positioning for rear lane entry."
    },
    "HAZMAT_WARNING": {
        "id": "HAZMAT_WARNING",
        "title": "🧪 Hazmat / Toxic Fumes Directive",
        "directive": "HAZMAT DIRECTIVE: Chemical odor and flammable vapor reported on site. Approach upwind from North. Don Level B respiratory masks before staging.",
        "badge": "HAZMAT PROTOCOL",
        "speed_boost": 0.0,
        "sample_ack": "Upwind approach confirmed. Crew donning SCBA respirators. Atmospheric gas analyzer armed."
    }
}


def generate_unit_tactical_acknowledgment(
    unit_name: str,
    call_sign: str,
    directive_text: str,
    directive_key: Optional[str] = None
) -> str:
    """Generate realistic tactical radio feedback from the vehicle's Mobile Data Terminal (MDT)."""
    unit_tag = call_sign or unit_name
    
    if directive_key and directive_key in TACTICAL_PRESET_DIRECTIVES:
        ack_body = TACTICAL_PRESET_DIRECTIVES[directive_key]["sample_ack"]
        return f"[{unit_tag} MDT]: {ack_body}"
        
    # Context-aware generated acknowledgment for custom orders
    lower_text = directive_text.lower()
    if any(k in lower_text for k in ["doctor", "bleed", "unconscious", "cpr", "oxygen", "breath", "blood", "medical", "cardiac"]):
        return f"[{unit_tag} MDT]: Understood dispatch. Paramedics briefed on vital deterioration. Trauma kit ready."
    elif any(k in lower_text for k in ["armed", "gun", "knife", "weapon", "hold", "stop", "wait", "standby", "perimeter"]):
        return f"[{unit_tag} MDT]: Roger dispatch. Holding outer perimeter, keeping safe standoff. Awaiting green light."
    elif any(k in lower_text for k in ["siren", "speed", "fast", "rush", "hurry", "quick", "expedite"]):
        return f"[{unit_tag} MDT]: Copy dispatch! Accelerating response, sirens active, cutting transit time."
    elif any(k in lower_text for k in ["door", "window", "rear", "back", "enter", "gate", "floor", "flat"]):
        return f"[{unit_tag} MDT]: Copy specific entry directive. Target structure noted, approaching designated access point."
    else:
        return f"[{unit_tag} MDT]: Transmission received and acknowledged. Operational directives applied to navigation computer."


def build_dispatch_tactical_map(
    incident: Any,
    unit: Any,
    assignment: Optional[Any] = None,
    is_dark: bool = True,
    zoom_start: int = 13,
    breadcrumbs: Optional[List[Tuple[float, float]]] = None
) -> folium.Map:
    """
    Build a high-contrast tactical mission corridor map centered on the active incident and assigned service vehicle.
    Features:
    - CartoDB dark_matter (dark mode) or CartoDB voyager (light mode)
    - Pulsing animated radar victim beacon with casualty hazard zone
    - High-visibility service vehicle marker with speed/status tag
    - Base station departure pin
    - Traveled GPS breadcrumbs
    - Glowing active route trajectory connecting vehicle to victim
    - Auto-fit bounds so both vehicle and victim are perfectly framed
    """
    inc_lat = getattr(incident, "latitude", None) or 28.6139
    inc_lon = getattr(incident, "longitude", None) or 77.2090
    urgency = getattr(incident, "current_urgency", "P1")
    urg_cfg = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["P1"])

    unit_lat = getattr(unit, "current_lat", inc_lat + 0.02)
    unit_lon = getattr(unit, "current_lon", inc_lon + 0.02)
    base_lat = getattr(unit, "base_lat", unit_lat)
    base_lon = getattr(unit, "base_lon", unit_lon)
    service_type = getattr(unit, "service_type", "police")
    srv_cfg = SERVICE_CONFIG.get(service_type, SERVICE_CONFIG["police"])
    unit_status = getattr(unit, "status", "en_route").upper()
    speed_kmh = getattr(unit, "speed_kmh", 55.0)

    # Center map midway between unit and incident
    mid_lat = (inc_lat + unit_lat) / 2.0
    mid_lon = (inc_lon + unit_lon) / 2.0

    tiles_url = DARK_TILES_URL if is_dark else LIGHT_TILES_URL
    m = folium.Map(
        location=[mid_lat, mid_lon],
        zoom_start=zoom_start,
        tiles=tiles_url,
        attr=CARTO_ATTR,
        control_scale=True
    )

    # 1. Casualty Hazard Zone (Translucent outer radius around victim)
    folium.Circle(
        location=[inc_lat, inc_lon],
        radius=350,
        color=urg_cfg["color"],
        fill=True,
        fill_color=urg_cfg["color"],
        fill_opacity=0.18,
        weight=1.5,
        dash_array="5, 8",
        tooltip=f"Casualty Hazard Zone (350m Perimeter): {incident.id}"
    ).add_to(m)

    # 2. Pulsing Victim Beacon DivIcon
    victim_div_html = f"""
    <div style="position: relative; width: 44px; height: 44px;">
        <div style="position: absolute; width: 44px; height: 44px; border-radius: 50%; background: {urg_cfg['pulse_color']}; box-shadow: 0 0 16px {urg_cfg['color']}; opacity: 0.85;"></div>
        <div style="position: absolute; top: 7px; left: 7px; width: 30px; height: 30px; border-radius: 50%; background: {urg_cfg['color']}; border: 2.5px solid #FFFFFF; display: flex; align-items: center; justify-content: center; font-size: 15px; font-weight: 800; color: white; box-shadow: 0 2px 8px rgba(0,0,0,0.4);">
            {urg_cfg['icon']}
        </div>
        <div style="position: absolute; top: 40px; left: -26px; width: 96px; text-align: center; background: rgba(15,23,42,0.92); color: #F8FAFC; border: 1px solid {urg_cfg['color']}; border-radius: 4px; font-size: 10px; font-weight: 800; padding: 1px 4px; white-space: nowrap; box-shadow: 0 2px 6px rgba(0,0,0,0.5);">
            VICTIM: {incident.id}
        </div>
    </div>
    """
    victim_popup_html = f"""
    <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; min-width: 220px; padding: 4px; color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: 900; font-size: 14px; color: {urg_cfg['color']};">{incident.id}</span>
            <span style="background: {urg_cfg['color']}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 800;">{urg_cfg['label']}</span>
        </div>
        <div style="margin-bottom: 4px; font-size: 11px; color: #475569;"><b>Threat:</b> {getattr(incident, 'primary_threat', 'Emergency')}</div>
        <div style="margin-bottom: 4px; font-size: 11px; color: #475569;"><b>Locality:</b> {getattr(incident, 'location_text', 'Pending')}</div>
        <div style="font-size: 10px; color: #64748B;">GPS: {inc_lat:.4f}, {inc_lon:.4f}</div>
    </div>
    """
    folium.Marker(
        location=[inc_lat, inc_lon],
        icon=folium.DivIcon(html=victim_div_html, icon_size=(44, 44), icon_anchor=(22, 22)),
        popup=folium.Popup(victim_popup_html, max_width=280),
        tooltip=f"Incident {incident.id} [{urg_cfg['label']}] - {getattr(incident, 'location_text', 'Scene')}"
    ).add_to(m)

    # 3. Base Station Departure Point Marker (if different from unit position)
    if abs(base_lat - unit_lat) > 0.001 or abs(base_lon - unit_lon) > 0.001:
        folium.CircleMarker(
            location=[base_lat, base_lon],
            radius=6,
            color="#64748B",
            fill=True,
            fill_color="#334155",
            fill_opacity=0.8,
            weight=2,
            tooltip=f"Base Station: {unit.unit_name} Departure Station"
        ).add_to(m)

        # Traveled Trail (Dotted subtle line from Base to Unit current location)
        folium.PolyLine(
            locations=[[base_lat, base_lon], [unit_lat, unit_lon]],
            color="#64748B",
            weight=2.5,
            opacity=0.6,
            dash_array="4, 6",
            tooltip="Traveled Path Vector"
        ).add_to(m)

    # 4. Service Vehicle Marker DivIcon
    vehicle_pulse = "box-shadow: 0 0 16px " + srv_cfg["color"] + ";" if unit_status in ["EN_ROUTE", "DISPATCHED"] else ""
    vehicle_div_html = f"""
    <div style="position: relative; width: 46px; height: 46px;">
        <div style="position: absolute; width: 46px; height: 46px; border-radius: 50%; background: {srv_cfg['glow']}; {vehicle_pulse}"></div>
        <div style="position: absolute; top: 6px; left: 6px; width: 34px; height: 34px; border-radius: 50%; background: {srv_cfg['color']}; border: 2.5px solid #FFFFFF; display: flex; align-items: center; justify-content: center; font-size: 18px; box-shadow: 0 4px 10px rgba(0,0,0,0.45);">
            {srv_cfg['emoji']}
        </div>
        <div style="position: absolute; top: 42px; left: -36px; width: 118px; text-align: center; background: rgba(15,23,42,0.95); color: #38BDF8; border: 1px solid #38BDF8; border-radius: 4px; font-size: 10px; font-weight: 800; padding: 1px 4px; white-space: nowrap; box-shadow: 0 2px 6px rgba(0,0,0,0.5);">
            {unit.unit_name} [{speed_kmh:.0f} km/h]
        </div>
    </div>
    """
    eta_mins = getattr(assignment, "eta_minutes", 0.0) if assignment else 0.0
    dist_km = getattr(assignment, "distance_km", 0.0) if assignment else 0.0
    vehicle_popup_html = f"""
    <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; min-width: 220px; padding: 4px; color: #0F172A;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
            <span style="font-weight: 900; font-size: 14px; color: {srv_cfg['color']};">{unit.unit_name}</span>
            <span style="background: {srv_cfg['badge_bg']}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; font-weight: 800;">{unit_status}</span>
        </div>
        <div style="font-size: 11px; color: #475569; margin-bottom: 2px;"><b>Service:</b> {srv_cfg['label']}</div>
        <div style="font-size: 11px; color: #475569; margin-bottom: 2px;"><b>Speed:</b> {speed_kmh:.1f} km/h</div>
        <div style="font-size: 11px; color: #475569; margin-bottom: 2px;"><b>Remaining Distance:</b> {dist_km:.1f} km</div>
        <div style="font-size: 11px; color: #0284C7; font-weight: 800; margin-bottom: 2px;"><b>ETA:</b> {eta_mins:.1f} mins</div>
        <div style="font-size: 10px; color: #64748B;">GPS: {unit_lat:.4f}, {unit_lon:.4f}</div>
    </div>
    """
    folium.Marker(
        location=[unit_lat, unit_lon],
        icon=folium.DivIcon(html=vehicle_div_html, icon_size=(46, 46), icon_anchor=(23, 23)),
        popup=folium.Popup(vehicle_popup_html, max_width=280),
        tooltip=f"{unit.unit_name} ({srv_cfg['label']}) - {unit_status} • ETA {eta_mins:.1f}m"
    ).add_to(m)

    # 5. Glowing Active Route Trajectory from Service Vehicle to Victim
    if abs(unit_lat - inc_lat) > 0.0005 or abs(unit_lon - inc_lon) > 0.0005:
        # Subtle glow underlay
        folium.PolyLine(
            locations=[[unit_lat, unit_lon], [inc_lat, inc_lon]],
            color=srv_cfg["color"],
            weight=7,
            opacity=0.35
        ).add_to(m)

        # Animated AntPath flowing trajectory
        AntPath(
            locations=[[unit_lat, unit_lon], [inc_lat, inc_lon]],
            color=srv_cfg["color"],
            pulse_color="#FFFFFF" if is_dark else "#1E293B",
            weight=4,
            opacity=0.9,
            dash_array=[10, 20],
            delay=800,
            tooltip=f"Active Corridor: {unit.unit_name} → Victim ({dist_km:.1f} km, ETA {eta_mins:.1f}m)"
        ).add_to(m)

        # Midpoint ETA Callout Tag
        mid_traj_lat = (unit_lat + inc_lat) / 2.0
        mid_traj_lon = (unit_lon + inc_lon) / 2.0
        eta_tag_html = f"""
        <div style="background: rgba(15,23,42,0.92); color: #38BDF8; border: 1px solid #38BDF8; border-radius: 12px; padding: 2px 8px; font-size: 10px; font-weight: 800; white-space: nowrap; box-shadow: 0 2px 6px rgba(0,0,0,0.5);">
            ⚡ {dist_km:.1f} km • ETA {eta_mins:.1f}m
        </div>
        """
        folium.Marker(
            location=[mid_traj_lat, mid_traj_lon],
            icon=folium.DivIcon(html=eta_tag_html, icon_size=(80, 20), icon_anchor=(40, 10))
        ).add_to(m)

    # 6. Auto-fit bounds with generous margin
    lats = [inc_lat, unit_lat, base_lat]
    lons = [inc_lon, unit_lon, base_lon]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)
    
    # Ensure minimum bounding box size
    if max_lat - min_lat < 0.015:
        min_lat -= 0.01
        max_lat += 0.01
    if max_lon - min_lon < 0.015:
        min_lon -= 0.01
        max_lon += 0.01

    m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=[30, 30])
    return m


def build_fleet_overview_map(
    incidents: List[Any],
    units: List[Any],
    dispatches: List[Any],
    is_dark: bool = True,
    zoom_start: int = 11
) -> folium.Map:
    """
    Build a comprehensive city-wide tactical emergency map for Delhi NCR.
    Plots all active incidents with pulsing beacons, all responder units,
    and active dispatch corridors.
    """
    tiles_url = DARK_TILES_URL if is_dark else LIGHT_TILES_URL
    m = folium.Map(
        location=[28.6250, 77.2000],
        zoom_start=zoom_start,
        tiles=tiles_url,
        attr=CARTO_ATTR,
        control_scale=True
    )

    # Unit Coordinates Index
    unit_map = {}
    for u in units:
        unit_map[u.id] = u
        srv_cfg = SERVICE_CONFIG.get(u.service_type, SERVICE_CONFIG["police"])
        status_label = u.status.upper().replace("_", " ")
        
        status_color = "#10B981" if u.status == "available" else ("#38BDF8" if u.status in ["assigned", "dispatched", "en_route"] else "#F59E0B")
        
        unit_div_html = f"""
        <div style="position: relative; width: 34px; height: 34px;">
            <div style="position: absolute; width: 34px; height: 34px; border-radius: 50%; background: {srv_cfg['color']}; border: 2px solid white; display: flex; align-items: center; justify-content: center; font-size: 15px; box-shadow: 0 2px 6px rgba(0,0,0,0.4);">
                {srv_cfg['emoji']}
            </div>
        </div>
        """
        popup_html = f"""
        <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; min-width: 190px; padding: 4px; color: #0F172A;">
            <div style="font-weight: 800; font-size: 14px; margin-bottom: 2px; color: {srv_cfg['color']};">{u.unit_name}</div>
            <div style="font-size: 11px; color: #64748B; margin-bottom: 6px;">Unit ID: {u.id} • {srv_cfg['label']}</div>
            <div style="margin-bottom: 4px;"><b>Status:</b> <span style="color: {status_color}; font-weight: 800;">{status_label}</span></div>
            <div style="margin-bottom: 2px;"><b>Speed:</b> {u.speed_kmh:.1f} km/h</div>
            <div style="font-size: 10px; color: #64748B;">GPS: {u.current_lat:.4f}, {u.current_lon:.4f}</div>
        </div>
        """
        folium.Marker(
            location=[u.current_lat, u.current_lon],
            icon=folium.DivIcon(html=unit_div_html, icon_size=(34, 34), icon_anchor=(17, 17)),
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"{u.unit_name} ({srv_cfg['label']}) - {status_label}"
        ).add_to(m)

    # Incident Coordinates Index
    incident_map = {}
    for inc in incidents:
        if inc.latitude and inc.longitude:
            incident_map[inc.id] = inc
            urgency = inc.current_urgency or "P1"
            urg_cfg = URGENCY_CONFIG.get(urgency, URGENCY_CONFIG["P1"])

            inc_div_html = f"""
            <div style="position: relative; width: 36px; height: 36px;">
                <div style="position: absolute; width: 36px; height: 36px; border-radius: 50%; background: {urg_cfg['pulse_color']}; box-shadow: 0 0 10px {urg_cfg['color']};"></div>
                <div style="position: absolute; top: 4px; left: 4px; width: 28px; height: 28px; border-radius: 50%; background: {urg_cfg['color']}; border: 2px solid white; display: flex; align-items: center; justify-content: center; font-size: 13px; color: white;">
                    {urg_cfg['icon']}
                </div>
            </div>
            """
            inc_popup_html = f"""
            <div style="font-family: system-ui, -apple-system, sans-serif; font-size: 12px; min-width: 200px; padding: 4px; color: #0F172A;">
                <div style="font-weight: 800; font-size: 14px; color: {urg_cfg['color']}; margin-bottom: 2px;">★ {inc.id}</div>
                <div style="font-size: 11px; color: #64748B; margin-bottom: 4px;"><b>Threat:</b> {inc.primary_threat or 'Emergency'}</div>
                <div style="margin-bottom: 4px;"><b>Urgency:</b> <span style="color: {urg_cfg['color']}; font-weight: 800;">{urg_cfg['label']}</span></div>
                <div style="margin-bottom: 2px;"><b>Locality:</b> {inc.location_text or 'Delhi NCR'}</div>
                <div><b>Status:</b> {inc.status.upper()}</div>
            </div>
            """
            folium.Marker(
                location=[inc.latitude, inc.longitude],
                icon=folium.DivIcon(html=inc_div_html, icon_size=(36, 36), icon_anchor=(18, 18)),
                popup=folium.Popup(inc_popup_html, max_width=280),
                tooltip=f"Incident {inc.id} [{urg_cfg['label']}] - {inc.location_text}"
            ).add_to(m)

    # Active Dispatch Mission Lines
    for disp in dispatches:
        if disp.status in ["assigned", "dispatched", "en_route"] and disp.incident_id in incident_map and disp.unit_id in unit_map:
            u = unit_map[disp.unit_id]
            inc = incident_map[disp.incident_id]
            srv_cfg = SERVICE_CONFIG.get(u.service_type, SERVICE_CONFIG["police"])
            AntPath(
                locations=[[u.current_lat, u.current_lon], [inc.latitude, inc.longitude]],
                color=srv_cfg["color"],
                pulse_color="#FFFFFF" if is_dark else "#0F172A",
                weight=3.5,
                opacity=0.85,
                dash_array=[8, 16],
                delay=1000,
                tooltip=f"Corridor: {u.unit_name} → {inc.id} ({disp.distance_km:.1f} km • ETA {disp.eta_minutes:.1f}m)"
            ).add_to(m)

    return m


def render_telemetry_hud(unit: Any, assignment: Any, is_dark: bool = True):
    """Render 4 responsive tactical telemetry metric cards for CAD dispatch."""
    import streamlit as st
    card_bg = "#111C2E" if is_dark else "#FFFFFF"
    card_border = "#1E293B" if is_dark else "#E2E8F0"
    label_color = "#94A3B8" if is_dark else "#64748B"
    text_color = "#F8FAFC" if is_dark else "#0F172A"
    accent_blue = "#38BDF8" if is_dark else "#0284C7"
    accent_green = "#34D399" if is_dark else "#059669"
    accent_amber = "#FBBF24" if is_dark else "#D97706"

    service_type = getattr(unit, "service_type", "police")
    srv_cfg = SERVICE_CONFIG.get(service_type, SERVICE_CONFIG["police"])
    speed = getattr(unit, "speed_kmh", 55.0)
    status = getattr(assignment, "status", "en_route").upper().replace("_", " ")
    dist_km = getattr(assignment, "distance_km", 0.0)
    eta_mins = getattr(assignment, "eta_minutes", 0.0)

    html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 12px; margin-bottom: 16px;">
        <!-- Card 1: Unit Telemetry -->
        <div style="flex: 1 1 200px; background: {card_bg}; border: 1px solid {card_border}; border-left: 4px solid {srv_cfg['color']}; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 11px; font-weight: 700; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em;">{srv_cfg['emoji']} {srv_cfg['label']}</div>
            <div style="font-size: 17px; font-weight: 800; color: {text_color}; margin-top: 2px;">{unit.unit_name}</div>
            <div style="font-size: 12px; color: {accent_blue}; font-weight: 700; margin-top: 2px;">
                Speed: {speed:.0f} km/h • <span style="color: {accent_amber};">{status}</span>
            </div>
        </div>

        <!-- Card 2: Remaining Distance -->
        <div style="flex: 1 1 180px; background: {card_bg}; border: 1px solid {card_border}; border-left: 4px solid #38BDF8; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 11px; font-weight: 700; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em;">📍 Remaining Distance</div>
            <div style="font-size: 22px; font-weight: 900; color: {text_color}; margin-top: 2px;">{dist_km:.2f} <span style="font-size: 13px; font-weight: 600; color: {label_color};">km</span></div>
            <div style="font-size: 11px; color: {label_color}; margin-top: 2px;">Route Vector to Scene</div>
        </div>

        <!-- Card 3: Dynamic Live ETA -->
        <div style="flex: 1 1 180px; background: {card_bg}; border: 1px solid {card_border}; border-left: 4px solid #F59E0B; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 11px; font-weight: 700; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em;">⏱️ Estimated Arrival</div>
            <div style="font-size: 22px; font-weight: 900; color: #F59E0B; margin-top: 2px;">{eta_mins:.1f} <span style="font-size: 13px; font-weight: 600; color: {label_color};">mins</span></div>
            <div style="font-size: 11px; color: {accent_green}; font-weight: 700; margin-top: 2px;">Live GPS Tracking</div>
        </div>

        <!-- Card 4: Tactical Link Status -->
        <div style="flex: 1 1 200px; background: {card_bg}; border: 1px solid {card_border}; border-left: 4px solid {accent_green}; border-radius: 8px; padding: 12px 14px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
            <div style="font-size: 11px; font-weight: 700; color: {label_color}; text-transform: uppercase; letter-spacing: 0.05em;">📡 Tactical CAD Link</div>
            <div style="font-size: 15px; font-weight: 800; color: {accent_green}; margin-top: 4px;">🟢 5G LINK CONNECTED</div>
            <div style="font-size: 11px; color: {label_color}; margin-top: 2px;">CH-04 TAC • Latency 14ms</div>
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_tactical_comms_console(
    db: Any,
    incident: Any,
    unit: Any,
    assignment: Any,
    is_dark: bool = True,
    actor_id: str = "Dispatcher"
):
    """
    Render the real-time Tactical Radio Communications & Escalation Command console.
    Allows dispatchers to transmit urgent escalation directives (Code 3, Hostile Scene, ALS Medical,
    Covert Approach, Hazmat), custom orders, and receives simulated real-time unit acknowledgments.
    """
    import streamlit as st
    from sahaay.audit import log_audit_event
    from sahaay.dispatch.simulation import escalate_unit_response

    if "dispatch_comms" not in st.session_state:
        st.session_state.dispatch_comms = {}

    if incident.id not in st.session_state.dispatch_comms:
        now_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
        st.session_state.dispatch_comms[incident.id] = [
            {
                "timestamp": now_str,
                "sender": "DISPATCH HQ",
                "badge": "MISSION DISPATCH",
                "text": f"Unit {unit.unit_name} ({unit.call_sign}) dispatched to Incident {incident.id}. Threat: {incident.primary_threat or 'Emergency'} at {incident.location_text or 'Delhi NCR'}.",
                "unit_ack": f"[{unit.call_sign} MDT]: Acknowledged. Rolling to scene with GPS navigation lock."
            }
        ]

    panel_bg = "#0F172A" if is_dark else "#FFFFFF"
    border_color = "#334155" if is_dark else "#CBD5E1"
    text_color = "#F8FAFC" if is_dark else "#0F172A"
    sub_color = "#94A3B8" if is_dark else "#64748B"

    st.markdown(
        f"""
        <div style="background: {panel_bg}; border: 1px solid {border_color}; border-radius: 8px; padding: 14px 18px; margin-top: 14px; margin-bottom: 14px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;">
                <div>
                    <span style="font-size: 16px; font-weight: 800; color: {text_color};">
                        📻 Tactical Radio Net — Field Unit Control (CH-04 Encrypted)
                    </span>
                    <div style="font-size: 12px; color: {sub_color}; margin-top: 2px;">
                        Duplex command channel with <b>{unit.unit_name} [{unit.call_sign}]</b> • Instruct crew if situation escalates
                    </div>
                </div>
                <div style="background: rgba(16, 185, 129, 0.15); border: 1px solid #10B981; color: #10B981; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: 800;">
                    🟢 DUPLEX ACTIVE • AES-256
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # 1. Situation Escalation Quick-Directives
    st.markdown(
        f"<div style='font-size: 13px; font-weight: 800; color: {text_color}; margin-bottom: 6px;'>🚨 SITUATION ESCALATION DIRECTIVES (1-CLICK ORDERS):</div>",
        unsafe_allow_html=True
    )

    btn_cols = st.columns(5)
    directives_list = list(TACTICAL_PRESET_DIRECTIVES.values())

    for i, d in enumerate(directives_list):
        with btn_cols[i]:
            if st.button(d["title"], key=f"btn_tac_{incident.id}_{d['id']}", use_container_width=True):
                now_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
                unit_ack = generate_unit_tactical_acknowledgment(unit.unit_name, unit.call_sign, d["directive"], d["id"])
                
                # Append to comms log
                st.session_state.dispatch_comms[incident.id].append({
                    "timestamp": now_str,
                    "sender": "DISPATCH HQ",
                    "badge": d["badge"],
                    "text": d["directive"],
                    "unit_ack": unit_ack
                })

                # If speed boost applies (e.g. Code 3)
                if d["speed_boost"] != 0.0:
                    escalate_unit_response(
                        db=db,
                        assignment_id=assignment.id,
                        code_3=d["speed_boost"] > 0,
                        speed_boost=abs(d["speed_boost"]),
                        actor_id=actor_id
                    )

                log_audit_event(
                    db=db,
                    actor_id=actor_id,
                    actor_role="dispatcher",
                    action="TACTICAL_RADIO_DIRECTIVE",
                    object_type="dispatch",
                    object_id=str(assignment.id),
                    after_state={"directive": d["id"], "unit_ack": unit_ack},
                    reason=f"Transmitted tactical directive {d['id']} to {unit.unit_name}"
                )
                st.success(f"Dispatched: {d['title']}")
                st.rerun()

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # 2. Custom Directive Input & Urgency Escalation
    col_input, col_esc = st.columns([3, 1], gap="small")

    with col_input:
        custom_msg = st.text_input(
            "Custom Tactical Directive to Vehicle MDT:",
            placeholder="Type tactical order (e.g. Victim hiding on 2nd floor, access via back gate)...",
            key=f"input_cmd_{incident.id}"
        )
        if st.button("🎙️ Transmit Directive to Field Unit", key=f"send_cmd_{incident.id}", type="primary"):
            if custom_msg.strip():
                now_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
                unit_ack = generate_unit_tactical_acknowledgment(unit.unit_name, unit.call_sign, custom_msg)
                st.session_state.dispatch_comms[incident.id].append({
                    "timestamp": now_str,
                    "sender": "DISPATCH HQ",
                    "badge": "TACTICAL DIRECTIVE",
                    "text": custom_msg.strip(),
                    "unit_ack": unit_ack
                })
                log_audit_event(
                    db=db,
                    actor_id=actor_id,
                    actor_role="dispatcher",
                    action="TACTICAL_RADIO_CUSTOM",
                    object_type="dispatch",
                    object_id=str(assignment.id),
                    after_state={"message": custom_msg.strip(), "unit_ack": unit_ack},
                    reason=f"Custom tactical directive sent to {unit.unit_name}"
                )
                st.success("Directive transmitted via tactical radio channel.")
                st.rerun()

    with col_esc:
        st.markdown("<div style='font-size: 12px; font-weight: 700; color: #EF4444; margin-bottom: 4px;'>⚠️ CASE ESCALATION</div>", unsafe_allow_html=True)
        next_urg_map = {"P3": "P2", "P2": "P1", "P1": "P0"}
        cur_urg = getattr(incident, "current_urgency", "P2")
        next_urg = next_urg_map.get(cur_urg, None)

        if next_urg:
            if st.button(f"🔺 Escalate to {next_urg} Critical", key=f"btn_urg_{incident.id}", use_container_width=True):
                incident.current_urgency = next_urg
                db.commit()
                # Escalate unit response speed
                escalate_unit_response(db, assignment.id, code_3=True, speed_boost=25.0, actor_id=actor_id)
                now_str = datetime.datetime.utcnow().strftime("%H:%M:%S UTC")
                esc_msg = f"EMERGENCY ESCALATION: Case priority upgraded from {cur_urg} to {next_urg} due to deteriorating scene situation!"
                esc_ack = f"[{unit.call_sign} MDT]: Critical upgrade to {next_urg} acknowledged! Full emergency protocols active."
                st.session_state.dispatch_comms[incident.id].append({
                    "timestamp": now_str,
                    "sender": "DISPATCH HQ",
                    "badge": f"ESCALATED TO {next_urg}",
                    "text": esc_msg,
                    "unit_ack": esc_ack
                })
                log_audit_event(
                    db=db,
                    actor_id=actor_id,
                    actor_role="dispatcher",
                    action="INCIDENT_URGENCY_ESCALATED_COMMS",
                    object_type="incident",
                    object_id=incident.id,
                    before_state={"urgency": cur_urg},
                    after_state={"urgency": next_urg},
                    reason="Dispatcher escalated incident priority via tactical comms"
                )
                st.warning(f"Incident escalated to {next_urg}! Field unit alerted.")
                st.rerun()
        else:
            st.info("Incident is at Maximum Priority (P0).")

    # 3. Live Comms Log Feed
    st.markdown(
        f"<div style='font-size: 13px; font-weight: 800; color: {text_color}; margin-top: 14px; margin-bottom: 8px;'>📜 TACTICAL RADIO TRANSMISSION AUDIT LOG:</div>",
        unsafe_allow_html=True
    )

    comms_history = st.session_state.dispatch_comms.get(incident.id, [])
    log_container = st.container()

    with log_container:
        for entry in reversed(comms_history):
            dispatch_card_bg = "#1E293B" if is_dark else "#F1F5F9"
            unit_card_bg = "#112233" if is_dark else "#F8FAFC"
            
            feed_html = f"""
            <div style="margin-bottom: 10px; border: 1px solid {border_color}; border-radius: 6px; overflow: hidden;">
                <!-- Dispatch Transmission -->
                <div style="background: {dispatch_card_bg}; padding: 8px 12px; border-left: 4px solid #38BDF8;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <span style="font-size: 11px; font-weight: 800; color: #38BDF8;">🎙️ {entry['sender']} &rarr; UNIT</span>
                        <span style="font-size: 10px; color: {sub_color};">{entry['timestamp']} • <span style="background: rgba(56,189,248,0.2); color: #38BDF8; padding: 1px 6px; border-radius: 3px; font-weight: 700;">{entry.get('badge', 'ORDER')}</span></span>
                    </div>
                    <div style="font-size: 12px; color: {text_color};">{entry['text']}</div>
                </div>

                <!-- Unit MDT Acknowledgment -->
                <div style="background: {unit_card_bg}; padding: 8px 12px; border-left: 4px solid #10B981; border-top: 1px dashed {border_color};">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">
                        <span style="font-size: 11px; font-weight: 800; color: #10B981;">📡 UNIT RESPONSE &rarr; DISPATCH</span>
                        <span style="font-size: 10px; color: #10B981; font-weight: 700;">✓ ACKNOWLEDGED BY MDT</span>
                    </div>
                    <div style="font-size: 12px; color: {text_color}; font-family: monospace;">{entry['unit_ack']}</div>
                </div>
            </div>
            """
            st.markdown(feed_html, unsafe_allow_html=True)

