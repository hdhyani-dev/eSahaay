"""Custom theme and visual identity for eSahaay Emergency Response & Triage System.
Modern enterprise emergency command center aesthetic (Motorola CAD / RapidSOS / Linear standard).
Supports both Dark CAD Workstation (24/7 low-eye-strain command room) and Clean Light Operations Console.
"""
from typing import Dict, Any

PALETTE_DARK = {
    "theme": "dark",
    "primary_navy": "#F1F5F9",      # Primary text for headings
    "secondary_blue": "#22D3EE",    # Primary Accent (Cyan)
    "accent_cyan": "#22D3EE",       # Primary Accent (Cyan)
    "critical_red": "#FF5C68",      # Critical Emergency
    "priority_amber": "#FBBF24",    # Warning
    "success_green": "#34D399",     # Success
    "main_background": "#0B1220",   # Main Canvas Background
    "panel_background": "#111C2E",  # Cards and Sidebar Background
    "card_surface": "#111C2E",      # Cards Background
    "elevated_surface": "#19283D",  # Elevated surfaces
    "card_border": "#304158",       # Borders
    "primary_text": "#F1F5F9",      # Primary Text
    "secondary_text": "#A8B6C9",    # Secondary Text
    "muted_text": "#64748B",        # Muted Text
    "borders": "#304158",           # Borders
    "borders_strong": "#415570",    # Strong Borders
    "header_bg": "#111C2E",
    "sidebar_bg": "#111C2E",
    "input_bg": "#19283D",
    "input_border": "#304158",
    "btn_secondary_bg": "#19283D",
    "btn_secondary_border": "#304158",
    "btn_secondary_text": "#F1F5F9",
    "sub_box_bg": "#19283D",
    "sub_box_border": "#304158",
}

PALETTE_LIGHT = {
    "theme": "light",
    "primary_navy": "#142238",      # Primary text for headings in light mode
    "secondary_blue": "#007F9E",    # Primary Accent (Cyan/Teal)
    "accent_cyan": "#007F9E",       # Primary Accent (Cyan/Teal)
    "critical_red": "#C62838",      # Critical Emergency
    "priority_amber": "#956000",    # Warning
    "success_green": "#08784E",     # Success
    "main_background": "#F3F6FA",   # Main Canvas Background
    "panel_background": "#FFFFFF",  # Cards and Sidebar Background
    "card_surface": "#FFFFFF",      # Cards Background
    "elevated_surface": "#E8EFF7",  # Elevated surfaces
    "card_border": "#CBD5E1",       # Borders
    "primary_text": "#142238",      # Primary Text
    "secondary_text": "#52647B",    # Secondary Text
    "muted_text": "#64748B",        # Muted Text
    "borders": "#CBD5E1",           # Borders
    "borders_strong": "#94A3B8",    # Strong Borders
    "header_bg": "#FFFFFF",
    "sidebar_bg": "#FFFFFF",
    "input_bg": "#FFFFFF",
    "input_border": "#CBD5E1",
    "btn_secondary_bg": "#E8EFF7",
    "btn_secondary_border": "#CBD5E1",
    "btn_secondary_text": "#142238",
    "sub_box_bg": "#E8EFF7",
    "sub_box_border": "#CBD5E1",
}

# Default backwards-compatible palette
PALETTE = PALETTE_DARK

def get_theme_css(mode: str = "dark") -> str:
    """Return high-end enterprise CAD stylesheet for eSahaay in dark or light mode."""
    p = PALETTE_LIGHT if mode == "light" else PALETTE_DARK
    is_dark = (mode != "light")

    if is_dark:
        # Dark mode: Sun border icon on button (to switch to light mode)
        theme_specific_styles = """
        /* Top Right Corner Theme Toggle: Sun squircle in Dark Mode */
        div.st-key-top_right_theme_toggle,
        div[class*="st-key-top_right_theme_toggle"],
        div[data-testid="stElementContainer"]:has(button[key="top_right_theme_toggle"]) {
            position: fixed !important;
            top: 16px !important;
            right: 24px !important;
            z-index: 99999999 !important;
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            min-height: 44px !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: auto !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        div.st-key-top_right_theme_toggle button,
        div[class*="st-key-top_right_theme_toggle"] button,
        button[key="top_right_theme_toggle"] {
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            min-height: 44px !important;
            border-radius: 13px !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            background-color: #141C2B !important;
            border: 1.5px solid #2B3950 !important;
            box-shadow: 0 3px 12px rgba(0, 0, 0, 0.5), inset 0 1px 0 rgba(255, 255, 255, 0.08) !important;
            transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
            pointer-events: auto !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        div.st-key-top_right_theme_toggle button:hover,
        div[class*="st-key-top_right_theme_toggle"] button:hover,
        button[key="top_right_theme_toggle"]:hover {
            border-color: #475A79 !important;
            background-color: #1A2438 !important;
            transform: scale(1.05) !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.6), 0 0 14px rgba(251, 191, 36, 0.35) !important;
        }

        div.st-key-top_right_theme_toggle button p,
        div.st-key-top_right_theme_toggle button div,
        div.st-key-top_right_theme_toggle button span,
        div[class*="st-key-top_right_theme_toggle"] button p,
        div[class*="st-key-top_right_theme_toggle"] button div,
        div[class*="st-key-top_right_theme_toggle"] button span {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 22px !important;
            line-height: 1 !important;
            color: #FBBF24 !important;
            visibility: visible !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }

        /* High-Contrast Tooltips in Dark Mode (Pure White text on deep CAD slate pill) */
        div[data-baseweb="tooltip"],
        div[role="tooltip"],
        div[data-testid="stTooltipContent"],
        div[class*="stTooltipContent"] {
            background-color: #0B1220 !important;
            border: 1.5px solid #304158 !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
        }
        div[data-baseweb="tooltip"] *,
        div[role="tooltip"] *,
        div[data-testid="stTooltipContent"] *,
        div[class*="stTooltipContent"] *,
        div[data-testid="stTooltipContent"] p,
        div[data-testid="stTooltipContent"] span,
        div[role="tooltip"] p,
        div[role="tooltip"] span,
        div[data-baseweb="tooltip"] p,
        div[data-baseweb="tooltip"] span {
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 600 !important;
        }

        .sahaay-header {
            background: #111C2E !important;
            color: #F1F5F9 !important;
            border: 1px solid #304158 !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.25) !important;
        }
        .sahaay-header * { color: #F1F5F9 !important; }
        .sahaay-brand-name { color: #F1F5F9 !important; }
        .sahaay-tagline { color: #A8B6C9 !important; }
        .system-status-capsule {
            color: #F1F5F9 !important;
            background: rgba(34, 211, 238, 0.08) !important;
            border: 1px solid rgba(34, 211, 238, 0.25) !important;
        }
        .operator-profile-pill {
            background: #19283D !important;
            color: #F1F5F9 !important;
            border: 1px solid #304158 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #111C2E !important;
            border-right: 1px solid #304158 !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
            color: #F1F5F9 !important;
        }
        .sidebar-category-header {
            color: #A8B6C9 !important;
        }
        .sidebar-user-card {
            background: #19283D !important;
            border: 1px solid #304158 !important;
            color: #F1F5F9 !important;
        }
        .transcript-chunk-final {
            background: #19283D !important;
            border: 1px solid #304158 !important;
            border-left: 3px solid #22D3EE !important;
            color: #F1F5F9 !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.2) !important;
        }
        .transcript-chunk-partial {
            background: rgba(25, 40, 61, 0.6) !important;
            border: 1px dashed #304158 !important;
            color: #A8B6C9 !important;
        }
        .transcript-translation-box {
            background: rgba(34, 211, 238, 0.08) !important;
            border-left: 2.5px solid #22D3EE !important;
            color: #F1F5F9 !important;
        }
        .transcript-translation-pill {
            background: rgba(34, 211, 238, 0.2) !important;
            color: #22D3EE !important;
        }
        .protocol-card {
            background: rgba(34, 211, 238, 0.08) !important;
            border: 1px solid rgba(34, 211, 238, 0.25) !important;
            border-left: 4px solid #22D3EE !important;
        }
        .protocol-card-phrase { color: #F1F5F9 !important; }
        .telemetry-subcard {
            background: #19283D !important;
            border: 1px solid #304158 !important;
            color: #F1F5F9 !important;
        }
        .fleet-unit-card {
            background: #19283D !important;
            border: 1px solid #304158 !important;
            color: #F1F5F9 !important;
        }
        .fleet-unit-card:hover {
            border-color: #415570 !important;
        }
        .fleet-badge-police {
            background: rgba(34, 211, 238, 0.15) !important;
            color: #22D3EE !important;
            border: 1px solid rgba(34, 211, 238, 0.35) !important;
        }
        .fleet-badge-ambulance {
            background: rgba(255, 92, 104, 0.15) !important;
            color: #FF5C68 !important;
            border: 1px solid rgba(255, 92, 104, 0.35) !important;
        }
        .fleet-badge-fire {
            background: rgba(251, 191, 36, 0.15) !important;
            color: #FBBF24 !important;
            border: 1px solid rgba(251, 191, 36, 0.35) !important;
        }
        .fleet-badge-shelter {
            background: rgba(168, 85, 247, 0.15) !important;
            color: #C084FC !important;
            border: 1px solid rgba(168, 85, 247, 0.35) !important;
        }
        """
    else:
        # Light mode: Black moon border icon on button (to switch to dark mode)
        theme_specific_styles = """
        /* Top Right Corner Theme Toggle: Black moon squircle in Light Mode */
        div.st-key-top_right_theme_toggle,
        div[class*="st-key-top_right_theme_toggle"],
        div[data-testid="stElementContainer"]:has(button[key="top_right_theme_toggle"]) {
            position: fixed !important;
            top: 16px !important;
            right: 24px !important;
            z-index: 99999999 !important;
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            min-height: 44px !important;
            margin: 0 !important;
            padding: 0 !important;
            pointer-events: auto !important;
            display: block !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        div.st-key-top_right_theme_toggle button,
        div[class*="st-key-top_right_theme_toggle"] button,
        button[key="top_right_theme_toggle"] {
            width: 44px !important;
            height: 44px !important;
            min-width: 44px !important;
            min-height: 44px !important;
            border-radius: 13px !important;
            padding: 0 !important;
            margin: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            cursor: pointer !important;
            background-color: #FFFFFF !important;
            border: 1.5px solid #CBD5E1 !important;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.08), inset 0 1px 0 rgba(255, 255, 255, 0.9) !important;
            transition: all 0.22s cubic-bezier(0.4, 0, 0.2, 1) !important;
            pointer-events: auto !important;
            visibility: visible !important;
            opacity: 1 !important;
        }

        div.st-key-top_right_theme_toggle button:hover,
        div[class*="st-key-top_right_theme_toggle"] button:hover,
        button[key="top_right_theme_toggle"]:hover {
            background-color: #F8FAFC !important;
            border-color: #94A3B8 !important;
            transform: scale(1.05) !important;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.12) !important;
        }

        div.st-key-top_right_theme_toggle button p,
        div.st-key-top_right_theme_toggle button div,
        div.st-key-top_right_theme_toggle button span,
        div[class*="st-key-top_right_theme_toggle"] button p,
        div[class*="st-key-top_right_theme_toggle"] button div,
        div[class*="st-key-top_right_theme_toggle"] button span {
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
            padding: 0 !important;
            font-size: 22px !important;
            line-height: 1 !important;
            color: #142238 !important;
            visibility: visible !important;
            opacity: 1 !important;
            font-weight: 700 !important;
        }

        /* High-Contrast Tooltips in Light Mode (Pure White text on deep CAD slate pill - 100% visible) */
        div[data-baseweb="tooltip"],
        div[role="tooltip"],
        div[data-testid="stTooltipContent"],
        div[class*="stTooltipContent"],
        div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]),
        div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]) > div,
        div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]) div {
            background-color: #0B1220 !important;
            border: 1.5px solid #304158 !important;
            border-radius: 8px !important;
            color: #FFFFFF !important;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
        }
        div[data-baseweb="tooltip"] *,
        div[role="tooltip"] *,
        div[data-testid="stTooltipContent"] *,
        div[class*="stTooltipContent"] *,
        div[data-testid="stTooltipContent"] p,
        div[data-testid="stTooltipContent"] span,
        div[role="tooltip"] p,
        div[role="tooltip"] span,
        div[data-baseweb="tooltip"] p,
        div[data-baseweb="tooltip"] span,
        div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]) p,
        div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]) span {
            color: #FFFFFF !important;
            font-size: 13px !important;
            font-weight: 600 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7) !important;
        }

        .sahaay-header {
            background: #FFFFFF !important;
            color: #142238 !important;
            border: 1px solid #CBD5E1 !important;
            box-shadow: 0 1px 6px -1px rgba(20, 34, 56, 0.05) !important;
        }
        .sahaay-header * { color: #142238 !important; }
        .sahaay-brand-name { color: #142238 !important; }
        .sahaay-tagline { color: #52647B !important; }
        .system-status-capsule {
            color: #142238 !important;
            background: rgba(0, 127, 158, 0.07) !important;
            border: 1px solid rgba(0, 127, 158, 0.22) !important;
        }
        .operator-profile-pill {
            background: #E8EFF7 !important;
            color: #142238 !important;
            border: 1px solid #CBD5E1 !important;
        }
        [data-testid="stSidebar"] {
            background-color: #FFFFFF !important;
            border-right: 1px solid #CBD5E1 !important;
        }
        [data-testid="stSidebar"] p, [data-testid="stSidebar"] span, [data-testid="stSidebar"] label {
            color: #142238 !important;
        }
        .sidebar-category-header {
            color: #475569 !important;
            font-weight: 700 !important;
        }
        .sidebar-user-card {
            background: #E8EFF7 !important;
            border: 1px solid #CBD5E1 !important;
            color: #142238 !important;
        }
        .sidebar-user-card * {
            color: #142238 !important;
        }
        .transcript-chunk-final {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            border-left: 3px solid #007F9E !important;
            color: #142238 !important;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05) !important;
        }
        .transcript-chunk-partial {
            background: #F3F6FA !important;
            border: 1px dashed #CBD5E1 !important;
            color: #52647B !important;
        }
        .transcript-translation-box {
            background: rgba(0, 127, 158, 0.06) !important;
            border-left: 2.5px solid #007F9E !important;
            color: #142238 !important;
        }
        .transcript-translation-pill {
            background: rgba(0, 127, 158, 0.15) !important;
            color: #007F9E !important;
        }
        .protocol-card {
            background: rgba(0, 127, 158, 0.06) !important;
            border: 1px solid rgba(0, 127, 158, 0.22) !important;
            border-left: 4px solid #007F9E !important;
        }
        .protocol-card-phrase { color: #142238 !important; }
        .telemetry-subcard {
            background: #E8EFF7 !important;
            border: 1px solid #CBD5E1 !important;
            color: #142238 !important;
        }
        .fleet-unit-card {
            background: #FFFFFF !important;
            border: 1px solid #CBD5E1 !important;
            color: #142238 !important;
        }
        .fleet-unit-card:hover {
            border-color: #94A3B8 !important;
        }
        .fleet-badge-police {
            background: rgba(0, 127, 158, 0.12) !important;
            color: #007F9E !important;
            border: 1px solid rgba(0, 127, 158, 0.3) !important;
        }
        .fleet-badge-ambulance {
            background: rgba(198, 40, 56, 0.12) !important;
            color: #C62838 !important;
            border: 1px solid rgba(198, 40, 56, 0.3) !important;
        }
        .fleet-badge-fire {
            background: rgba(149, 96, 0, 0.12) !important;
            color: #956000 !important;
            border: 1px solid rgba(149, 96, 0, 0.3) !important;
        }
        .fleet-badge-shelter {
            background: rgba(147, 51, 234, 0.12) !important;
            color: #7E22CE !important;
            border: 1px solid rgba(168, 85, 247, 0.3) !important;
        }
        """

    return f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=Noto+Sans+Devanagari:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600&display=swap');

    /* Typography & Base Reset (Inter preferred with clean sans-serif fallbacks) */
    html, body, p, span, div, label, input, textarea, button {{
        font-family: 'Inter', 'Noto Sans Devanagari', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
        -webkit-font-smoothing: antialiased;
        -moz-osx-font-smoothing: grayscale;
    }}

    
    /* Hide Streamlit Toolbar to keep top-right theme toggle completely unobstructed */
    [data-testid="stToolbar"] {{
        display: none !important;
        visibility: hidden !important;
    }}
    header[data-testid="stHeader"] {{
        pointer-events: none !important;
    }}

    /* Hide Streamlit Hamburger Menu & Footer */
    #MainMenu {{ visibility: hidden !important; }}
    header[data-testid="stHeader"] {{ background: transparent !important; }}
    footer {{ visibility: hidden !important; }}

    /* Code & Telemetry Monospace */
    code, pre, .mono-data {{
        font-family: 'JetBrains Mono', monospace !important;
    }}

    /* Main Application Canvas */
    .stApp {{
        background-color: {p["main_background"]} !important;
        color: {p["primary_text"]} !important;
    }}

    /* Completely hide native audio player widgets (ringtone plays purely audibly) */
    div[data-testid="stAudio"], audio[controls] {{
        display: none !important;
        width: 0 !important;
        height: 0 !important;
        visibility: hidden !important;
    }}

    /* Content Typography */
    p, span, label, [data-testid="stMarkdownContainer"] p {{
        color: {p["primary_text"]};
        line-height: 1.55;
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: {p["primary_navy"]} !important;
        font-weight: 700 !important;
        letter-spacing: -0.025em !important;
    }}

    /* Top Enterprise App-Bar */
    .sahaay-header {{
        padding: 12px 24px !important;
        border-radius: 12px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        margin-bottom: 20px !important;
    }}

    .sahaay-brand-title {{
        display: flex !important;
        align-items: center !important;
        gap: 14px !important;
    }}

    .sahaay-brand-name {{
        font-size: 19px !important;
        font-weight: 800 !important;
        letter-spacing: 0.04em !important;
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
    }}

    .sahaay-tagline {{
        font-size: 11.5px !important;
        font-weight: 500 !important;
        letter-spacing: 0.02em !important;
    }}

    /* Status Capsule */
    .system-status-capsule {{
        display: flex !important;
        align-items: center !important;
        gap: 8px !important;
        font-size: 12px !important;
        padding: 6px 14px !important;
        border-radius: 9999px !important;
        letter-spacing: 0.02em !important;
    }}

    .live-pulse-dot {{
        height: 8px !important;
        width: 8px !important;
        background-color: {'#34D399' if is_dark else '#08784E'} !important;
        border-radius: 13px !important;
        display: inline-block !important;
        box-shadow: 0 0 8px {'#34D399' if is_dark else '#08784E'} !important;
    }}

    /* Operator Profile Pill */
    .operator-profile-pill {{
        display: flex !important;
        align-items: center !important;
        gap: 10px !important;
        padding: 5px 14px !important;
        border-radius: 9999px !important;
        font-size: 12.5px !important;
    }}

    .operator-avatar {{
        width: 24px !important;
        height: 24px !important;
        background: {'#0891B2' if is_dark else '#007F9E'} !important;
        color: #FFFFFF !important;
        border-radius: 13px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: center !important;
        font-size: 11px !important;
        font-weight: 700 !important;
    }}

    .sidebar-category-header {{
        font-size: 10.5px !important;
        font-weight: 700 !important;
        text-transform: uppercase !important;
        letter-spacing: 0.08em !important;
        margin: 18px 0 6px 4px !important;
    }}

    
    /* Sidebar Navigation Button Styles (Civic Command Center Solid Accent) */
    [data-testid="stSidebar"] button[kind="primary"],
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"],
    [data-testid="stSidebar"] .stButton > button[kind="primary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] {{
        background: {'#0891B2' if is_dark else '#007F9E'} !important;
        background-color: {'#0891B2' if is_dark else '#007F9E'} !important;
        color: #FFFFFF !important;
        border: 1px solid {'#22D3EE' if is_dark else '#006882'} !important;
        border-radius: 12px !important;
        box-shadow: 0 2px 8px {'rgba(8, 145, 178, 0.4)' if is_dark else 'rgba(0, 127, 158, 0.25)'} !important;
        font-weight: 700 !important;
        padding: 11px 16px !important;
        font-size: 13.5px !important;
        letter-spacing: 0.01em !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }}
    [data-testid="stSidebar"] button[kind="primary"] *,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"] *,
    [data-testid="stSidebar"] .stButton > button[kind="primary"] *,
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-primary"] * {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}
    [data-testid="stSidebar"] button[kind="primary"]:hover,
    [data-testid="stSidebar"] button[kind="primary"]:focus,
    [data-testid="stSidebar"] button[kind="primary"]:active,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:focus,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:active {{
        background: {'#0E7490' if is_dark else '#006882'} !important;
        background-color: {'#0E7490' if is_dark else '#006882'} !important;
        color: #FFFFFF !important;
        border-color: {'#22D3EE' if is_dark else '#006882'} !important;
        box-shadow: 0 3px 10px {'rgba(8, 145, 178, 0.5)' if is_dark else 'rgba(0, 127, 158, 0.35)'} !important;
    }}
    [data-testid="stSidebar"] button[kind="primary"]:hover *,
    [data-testid="stSidebar"] button[kind="primary"]:focus *,
    [data-testid="stSidebar"] button[kind="primary"]:active *,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:hover *,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:focus *,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-primary"]:active * {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"],
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"],
    [data-testid="stSidebar"] .stButton > button[kind="secondary"],
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] {{
        background: transparent !important;
        background-color: transparent !important;
        color: {'#CBD5E1' if is_dark else '#142238'} !important;
        border: 1px solid transparent !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        padding: 11px 16px !important;
        font-size: 13.5px !important;
        box-shadow: none !important;
        letter-spacing: 0.01em !important;
        transition: all 0.15s ease !important;
        justify-content: flex-start !important;
        text-align: left !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"] *,
    [data-testid="stSidebar"] button[data-testid="stBaseButton-secondary"] *,
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] *,
    [data-testid="stSidebar"] .stButton > button[data-testid="stBaseButton-secondary"] * {{
        color: {'#CBD5E1' if is_dark else '#142238'} !important;
        font-weight: 600 !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"]:hover,
    [data-testid="stSidebar"] button[kind="secondary"]:focus,
    [data-testid="stSidebar"] button[kind="secondary"]:active {{
        background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 127, 158, 0.08)'} !important;
        color: {'#FFFFFF' if is_dark else '#007F9E'} !important;
    }}
    [data-testid="stSidebar"] button[kind="secondary"]:hover *,
    [data-testid="stSidebar"] button[kind="secondary"]:focus *,
    [data-testid="stSidebar"] button[kind="secondary"]:active * {{
        color: {'#FFFFFF' if is_dark else '#007F9E'} !important;
    }}

    /* Modern Enterprise Buttons (Civic Command Center Accent) */
    button[data-testid="stBaseButton-primary"], button[kind="primary"], .stButton > button[kind="primary"] {{
        background: {'#0891B2' if is_dark else '#007F9E'} !important;
        color: #FFFFFF !important;
        border: 1px solid {'#22D3EE' if is_dark else '#006882'} !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 2px 6px 0 rgba(0, 0, 0, 0.25) !important;
        transition: all 0.15s ease-in-out !important;
    }}

    button[data-testid="stBaseButton-primary"] *, button[kind="primary"] *, .stButton > button[kind="primary"] * {{
        color: #FFFFFF !important;
    }}

    button[data-testid="stBaseButton-primary"]:hover, button[kind="primary"]:hover {{
        background: {'#0E7490' if is_dark else '#006882'} !important;
        box-shadow: 0 3px 8px 0 rgba(0, 0, 0, 0.35) !important;
        transform: translateY(-0.5px) !important;
    }}

    button[data-testid="stBaseButton-secondary"], button[kind="secondary"], .stButton > button[kind="secondary"], .stButton > button {{
        background: {p["btn_secondary_bg"]} !important;
        color: {p["btn_secondary_text"]} !important;
        border: 1px solid {p["btn_secondary_border"]} !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        letter-spacing: -0.01em !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1) !important;
        transition: all 0.15s ease-in-out !important;
    }}

    button[data-testid="stBaseButton-secondary"] *, button[kind="secondary"] *, .stButton > button * {{
        color: {p["btn_secondary_text"]} !important;
    }}

    button[data-testid="stBaseButton-secondary"]:hover, button[kind="secondary"]:hover, .stButton > button:hover {{
        background: {p["card_border"]} !important;
        border-color: {p["borders_strong"]} !important;
        transform: translateY(-0.5px) !important;
    }}

    /* Form Controls & Filter Inputs (High Contrast in both Dark & Light Themes) */
    div[data-testid="stTextInput"] label,
    div[data-testid="stTextInput"] label p,
    div[data-testid="stSelectbox"] label,
    div[data-testid="stSelectbox"] label p {{
        color: {'#F1F5F9' if is_dark else '#142238'} !important;
        font-weight: 700 !important;
        font-size: 13px !important;
        letter-spacing: -0.01em !important;
    }}

    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"],
    div[data-baseweb="input"],
    div[data-baseweb="base-input"] {{
        background-color: {'#19283D' if is_dark else '#FFFFFF'} !important;
        border: 1.5px solid {'#304158' if is_dark else '#CBD5E1'} !important;
        border-radius: 8px !important;
    }}

    div[data-testid="stTextInput"] input,
    div[data-baseweb="input"] input,
    input, textarea {{
        background-color: transparent !important;
        color: {'#F1F5F9' if is_dark else '#000000'} !important;
        caret-color: {'#22D3EE' if is_dark else '#000000'} !important;
        cursor: text !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
    }}

    div[data-testid="stTextInput"] div[data-baseweb="input"],
    div[data-testid="stTextInput"] div[data-baseweb="base-input"] {{
        cursor: text !important;
    }}

    /* Search History input - ensure jet-black cursor and text in light mode */
    div[data-testid="stTextInput"]:has(input[placeholder*="Search"]) input,
    div[data-testid="stTextInput"]:has(input[aria-label*="Search"]) input,
    input[placeholder*="Search"],
    input[aria-label*="Search"],
    input[type="text"] {{
        color: {'#F1F5F9' if is_dark else '#000000'} !important;
        caret-color: {'#22D3EE' if is_dark else '#000000'} !important;
        cursor: text !important;
    }}

    div[data-testid="stTextInput"] input::placeholder,
    div[data-baseweb="input"] input::placeholder,
    input::placeholder,
    textarea::placeholder {{
        color: {'#94A3B8' if is_dark else '#64748B'} !important;
        opacity: 1 !important;
        font-weight: 400 !important;
    }}

    div[data-testid="stSelectbox"] div[data-baseweb="select"],
    div[data-baseweb="select"],
    div[data-baseweb="select"] > div {{
        background-color: {'#19283D' if is_dark else '#FFFFFF'} !important;
        border: 1.5px solid {'#304158' if is_dark else '#CBD5E1'} !important;
        border-radius: 8px !important;
        color: {'#F1F5F9' if is_dark else '#142238'} !important;
    }}

    div[data-baseweb="select"] div,
    div[data-baseweb="select"] span,
    div[data-baseweb="select"] p,
    div[data-baseweb="select"] * {{
        color: {'#F1F5F9' if is_dark else '#142238'} !important;
        font-size: 13.5px !important;
        font-weight: 500 !important;
    }}

    div[data-baseweb="select"] svg {{
        fill: {'#A8B6C9' if is_dark else '#52647B'} !important;
        color: {'#A8B6C9' if is_dark else '#52647B'} !important;
    }}

    div[data-baseweb="popover"],
    div[data-baseweb="popover"] > div,
    ul[role="listbox"] {{
        background-color: {'#19283D' if is_dark else '#FFFFFF'} !important;
        color: {'#F1F5F9' if is_dark else '#142238'} !important;
        border: 1px solid {'#304158' if is_dark else '#CBD5E1'} !important;
        border-radius: 8px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, {'0.4' if is_dark else '0.12'}) !important;
    }}

    div[data-baseweb="popover"] p,
    div[data-baseweb="popover"] span,
    div[data-baseweb="popover"] div,
    div[data-baseweb="popover"] label {{
        color: {'#F1F5F9' if is_dark else '#142238'} !important;
    }}

    /* Global Tooltip & Help Hover Container Styling - Always High Contrast White on Dark */
    div[data-baseweb="tooltip"],
    div[role="tooltip"],
    div[data-testid="stTooltipContent"],
    div[class*="stTooltipContent"],
    div[data-testid="stTooltipContent"] > div,
    div[data-testid="stTooltipContent"] [data-testid="stMarkdownContainer"],
    div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]),
    div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]) div {{
        background-color: #0B1220 !important;
        color: #FFFFFF !important;
        border-color: #304158 !important;
    }}

    div[data-baseweb="tooltip"],
    div[role="tooltip"],
    div[data-testid="stTooltipContent"],
    div[class*="stTooltipContent"] {{
        border: 1.5px solid #304158 !important;
        border-radius: 8px !important;
        box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6) !important;
        padding: 6px 12px !important;
    }}

    div[data-baseweb="tooltip"] *,
    div[role="tooltip"] *,
    div[data-testid="stTooltipContent"] *,
    div[class*="stTooltipContent"] *,
    div[data-baseweb="popover"] [data-testid="stTooltipContent"] *,
    div[data-baseweb="tooltip"] p,
    div[role="tooltip"] p,
    div[data-testid="stTooltipContent"] p,
    div[data-baseweb="tooltip"] span,
    div[role="tooltip"] span,
    div[data-testid="stTooltipContent"] span,
    div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]) p,
    div[data-baseweb="popover"]:has([data-testid="stTooltipContent"]) span {{
        color: #FFFFFF !important;
        font-size: 13px !important;
        font-weight: 600 !important;
        line-height: 1.4 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.7) !important;
    }}

    div[data-baseweb="tooltip"] svg,
    div[role="tooltip"] svg {{
        fill: #0B1220 !important;
    }}

    li[role="option"] {{
        background-color: transparent !important;
        color: {'#F1F5F9' if is_dark else '#142238'} !important;
        font-size: 13px !important;
        font-weight: 500 !important;
        padding: 8px 14px !important;
    }}

    li[role="option"] * {{
        color: {'#F1F5F9' if is_dark else '#142238'} !important;
    }}

    li[role="option"]:hover,
    li[role="option"][aria-selected="true"] {{
        background-color: {'#111C2E' if is_dark else '#E8EFF7'} !important;
        color: {'#22D3EE' if is_dark else '#007F9E'} !important;
    }}

    li[role="option"]:hover *,
    li[role="option"][aria-selected="true"] * {{
        color: {'#22D3EE' if is_dark else '#007F9E'} !important;
        font-weight: 600 !important;
    }}

    /* Card Surfaces */
    .sahaay-card {{
        background: {p["card_surface"]} !important;
        border: 1px solid {p["card_border"]} !important;
        border-radius: 12px !important;
        padding: 20px 24px !important;
        margin-bottom: 16px !important;
        box-shadow: 0 4px 14px 0 rgba(0, 0, 0, {'0.25' if is_dark else '0.05'}) !important;
    }}

    .sahaay-card-title {{
        font-size: 15px !important;
        font-weight: 700 !important;
        color: {p["primary_text"]} !important;
        letter-spacing: -0.01em !important;
        margin-bottom: 8px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
    }}

    .sahaay-card-subtext {{
        font-size: 13px !important;
        color: {p["secondary_text"]} !important;
        line-height: 1.5 !important;
    }}

    /* Minimalist Metric Stat Card */
    .sahaay-kpi-card {{
        background: {p["card_surface"]} !important;
        border: 1px solid {p["card_border"]} !important;
        border-radius: 12px !important;
        padding: 18px 20px !important;
        box-shadow: 0 4px 12px 0 rgba(0, 0, 0, {'0.2' if is_dark else '0.05'}) !important;
        position: relative !important;
        overflow: hidden !important;
    }}

    .sahaay-kpi-label {{
        font-size: 11.5px !important;
        font-weight: 600 !important;
        color: {p["secondary_text"]} !important;
        text-transform: uppercase !important;
        letter-spacing: 0.05em !important;
    }}

    .sahaay-kpi-value {{
        font-size: 26px !important;
        font-weight: 800 !important;
        color: {p["primary_text"]} !important;
        letter-spacing: -0.03em !important;
        margin: 4px 0 2px 0 !important;
        font-variant-numeric: tabular-nums !important;
    }}

    .sahaay-kpi-footer {{
        font-size: 12px !important;
        color: {'#34D399' if is_dark else '#08784E'} !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        gap: 4px !important;
    }}

    /* Minimalist High-Contrast Status Badges (eSahaay Civic Command Center) */
    .badge-p0 {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 4px 10px !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        background: {'rgba(255, 92, 104, 0.15)' if is_dark else 'rgba(198, 40, 56, 0.12)'} !important;
        color: {'#FF5C68' if is_dark else '#C62838'} !important;
        border: 1px solid {'rgba(255, 92, 104, 0.4)' if is_dark else 'rgba(198, 40, 56, 0.35)'} !important;
    }}

    .badge-p0-dot {{
        width: 6px !important;
        height: 6px !important;
        border-radius: 13px !important;
        background-color: {'#FF5C68' if is_dark else '#C62838'} !important;
        box-shadow: 0 0 6px {'#FF5C68' if is_dark else '#C62838'} !important;
    }}

    .badge-p1 {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 4px 10px !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        background: {'rgba(251, 191, 36, 0.15)' if is_dark else 'rgba(149, 96, 0, 0.12)'} !important;
        color: {'#FBBF24' if is_dark else '#956000'} !important;
        border: 1px solid {'rgba(251, 191, 36, 0.4)' if is_dark else 'rgba(149, 96, 0, 0.35)'} !important;
    }}

    .badge-p1-dot {{
        width: 6px !important;
        height: 6px !important;
        border-radius: 13px !important;
        background-color: {'#FBBF24' if is_dark else '#956000'} !important;
    }}

    .badge-p2 {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 4px 10px !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        background: {'rgba(34, 211, 238, 0.15)' if is_dark else 'rgba(0, 127, 158, 0.12)'} !important;
        color: {'#22D3EE' if is_dark else '#007F9E'} !important;
        border: 1px solid {'rgba(34, 211, 238, 0.4)' if is_dark else 'rgba(0, 127, 158, 0.35)'} !important;
    }}

    .badge-p2-dot {{
        width: 6px !important;
        height: 6px !important;
        border-radius: 13px !important;
        background-color: {'#22D3EE' if is_dark else '#007F9E'} !important;
    }}

    .badge-p3 {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 4px 10px !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        background: {'rgba(168, 182, 201, 0.12)' if is_dark else 'rgba(82, 100, 123, 0.10)'} !important;
        color: {'#A8B6C9' if is_dark else '#52647B'} !important;
        border: 1px solid {'rgba(168, 182, 201, 0.3)' if is_dark else 'rgba(82, 100, 123, 0.25)'} !important;
    }}

    .badge-p3-dot {{
        width: 6px !important;
        height: 6px !important;
        border-radius: 13px !important;
        background-color: {'#A8B6C9' if is_dark else '#52647B'} !important;
    }}

    .badge-evaluating {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 4px 10px !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        background: {'rgba(34, 211, 238, 0.15)' if is_dark else 'rgba(0, 127, 158, 0.12)'} !important;
        color: {'#22D3EE' if is_dark else '#007F9E'} !important;
        border: 1px solid {'rgba(34, 211, 238, 0.4)' if is_dark else 'rgba(0, 127, 158, 0.35)'} !important;
    }}

    .badge-eval-dot {{
        width: 6px !important;
        height: 6px !important;
        border-radius: 13px !important;
        background-color: {'#22D3EE' if is_dark else '#007F9E'} !important;
        box-shadow: 0 0 6px {'#22D3EE' if is_dark else '#007F9E'} !important;
    }}

    .badge-standby {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 4px 10px !important;
        border-radius: 9999px !important;
        font-size: 11px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
        background: {'rgba(168, 182, 201, 0.12)' if is_dark else 'rgba(82, 100, 123, 0.10)'} !important;
        color: {'#A8B6C9' if is_dark else '#52647B'} !important;
        border: 1px solid {'rgba(168, 182, 201, 0.3)' if is_dark else 'rgba(82, 100, 123, 0.25)'} !important;
    }}

    .badge-standby-dot {{
        width: 6px !important;
        height: 6px !important;
        border-radius: 13px !important;
        background-color: {'#A8B6C9' if is_dark else '#52647B'} !important;
    }}

    /* Audio Waveform Bar Simulation */
    .audio-waveform-container {{
        display: flex !important;
        align-items: center !important;
        gap: 3px !important;
        height: 20px !important;
    }}

    .waveform-bar {{
        width: 3px !important;
        background: {'#22D3EE' if is_dark else '#007F9E'} !important;
        border-radius: 2px !important;
        animation: pulseWave 1s infinite ease-in-out alternate !important;
    }}

    @keyframes pulseWave {{
        0% {{ height: 4px; opacity: 0.4; }}
        100% {{ height: 18px; opacity: 1; }}
    }}

    /* Progressive Live Transcript */
    .transcript-chunk-final {{
        border-left: 3px solid #3B82F6 !important;
        border-radius: 8px !important;
        padding: 10px 14px !important;
        margin-bottom: 8px !important;
        font-size: 13.5px !important;
        line-height: 1.5 !important;
    }}

    .transcript-chunk-partial {{
        border-radius: 8px !important;
        padding: 10px 14px !important;
        font-size: 13px !important;
        font-style: italic !important;
    }}

    .transcript-translation-box {{
        margin-top: 8px !important;
        padding: 6px 10px !important;
        border-radius: 6px !important;
        font-size: 12.5px !important;
        display: flex !important;
        align-items: flex-start !important;
        gap: 8px !important;
    }}

    .transcript-translation-pill {{
        font-weight: 700 !important;
        font-size: 10px !important;
        letter-spacing: 0.05em !important;
        text-transform: uppercase !important;
        padding: 1px 6px !important;
        border-radius: 4px !important;
        white-space: nowrap !important;
    }}

    /* Suggested Protocol Box */
    .protocol-card {{
        border-radius: 8px !important;
        padding: 14px 18px !important;
        margin-top: 12px !important;
    }}

    .protocol-card-header {{
        font-size: 11px !important;
        font-weight: 700 !important;
        color: {'#22D3EE' if is_dark else '#007F9E'} !important;
        text-transform: uppercase !important;
        letter-spacing: 0.06em !important;
    }}

    .protocol-card-phrase {{
        font-size: 14.5px !important;
        font-weight: 600 !important;
        margin-top: 4px !important;
        line-height: 1.5 !important;
    }}

    /* Fleet Responder Unit Card */
    .fleet-unit-card {{
        border-radius: 10px !important;
        padding: 12px 14px !important;
        margin-bottom: 10px !important;
        display: flex !important;
        align-items: center !important;
        justify-content: space-between !important;
        transition: border-color 0.15s ease !important;
    }}

    .fleet-badge-police, .fleet-badge-ambulance, .fleet-badge-fire, .fleet-badge-shelter {{
        padding: 2px 8px !important;
        border-radius: 4px !important;
        font-size: 10.5px !important;
        font-weight: 700 !important;
        letter-spacing: 0.04em !important;
    }}

    /* Completely suppress Streamlit sidebar collapse button, header, and sidebar keyboard_double tooltips */
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarHeader"],
    [data-testid="collapsedControl"],
    button[aria-label*="sidebar" i],
    button[aria-label*="Close" i],
    button[aria-label*="Open" i],
    [data-testid="stSidebar"] div[data-baseweb="tooltip"],
    [data-testid="stSidebar"] div[data-baseweb="popover"],
    [data-testid="stSidebar"] div[role="tooltip"] {{
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
        width: 0 !important;
        height: 0 !important;
        margin: 0 !important;
        padding: 0 !important;
        overflow: hidden !important;
    }}

    [data-testid="stSidebarUserContent"] {{
        padding-top: 1rem !important;
    }}

    .sidebar-brand-box {{
        position: relative !important;
        z-index: 10 !important;
    }}

    .sidebar-logo-container {{
        padding: 4px 0 12px 0 !important;
        border-bottom: 1px solid rgba(148, 163, 184, 0.2) !important;
        margin-bottom: 12px !important;
        text-align: center !important;
        position: relative !important;
    }}

    .sidebar-logo-container img {{
        pointer-events: none !important;
        user-select: none !important;
        -webkit-user-drag: none !important;
    }}

    /* Modern CAD Navigation Buttons in Sidebar */
    [data-testid="stSidebar"] .stButton > button {{
        justify-content: flex-start !important;
        text-align: left !important;
        padding: 8px 12px !important;
        font-size: 12.5px !important;
        font-weight: 600 !important;
        border-radius: 8px !important;
        margin-bottom: 3px !important;
        transition: all 0.15s ease !important;
    }}

    [data-testid="stSidebar"] .stButton > button[kind="primary"] {{
        background: {'#0891B2' if is_dark else '#007F9E'} !important;
        color: #FFFFFF !important;
        border: 1px solid {'#22D3EE' if is_dark else '#006882'} !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="primary"] * {{
        color: #FFFFFF !important;
        font-weight: 700 !important;
    }}

    [data-testid="stSidebar"] .stButton > button[kind="secondary"] {{
        background: transparent !important;
        color: {'#CBD5E1' if is_dark else '#142238'} !important;
        border: 1px solid transparent !important;
    }}
    [data-testid="stSidebar"] .stButton > button[kind="secondary"] * {{
        color: {'#CBD5E1' if is_dark else '#142238'} !important;
    }}

    [data-testid="stSidebar"] .stButton > button[kind="secondary"]:hover {{
        background: {'rgba(255, 255, 255, 0.08)' if is_dark else 'rgba(0, 127, 158, 0.08)'} !important;
        color: {'#FFFFFF' if is_dark else '#007F9E'} !important;
    }}

    /* Case History Dossier UI System */
    .case-card {{
        border-radius: 10px !important;
        padding: 16px 20px !important;
        margin-bottom: 12px !important;
        transition: transform 0.12s ease, border-color 0.12s ease !important;
    }}
    .case-card:hover {{
        border-color: {'#22D3EE' if is_dark else '#007F9E'} !important;
    }}

    /* Dispatch Trajectory Timeline */
    .dispatch-timeline {{
        position: relative !important;
        padding-left: 24px !important;
        margin: 14px 0 !important;
    }}
    .dispatch-timeline::before {{
        content: '' !important;
        position: absolute !important;
        left: 7px !important;
        top: 6px !important;
        bottom: 6px !important;
        width: 2px !important;
        background: {'rgba(34, 211, 238, 0.35)' if is_dark else 'rgba(0, 127, 158, 0.3)'} !important;
    }}
    .timeline-node {{
        position: relative !important;
        margin-bottom: 14px !important;
    }}
    .timeline-dot {{
        position: absolute !important;
        left: -24px !important;
        top: 4px !important;
        width: 16px !important;
        height: 16px !important;
        border-radius: 13px !important;
        background: {'#111C2E' if is_dark else '#FFFFFF'} !important;
        border: 3px solid {'#22D3EE' if is_dark else '#007F9E'} !important;
    }}
    .timeline-dot.completed {{
        border-color: {'#34D399' if is_dark else '#08784E'} !important;
        background: {'#34D399' if is_dark else '#08784E'} !important;
    }}

    /* Conclusion Outcome Pills */
    .conclusion-pill {{
        display: inline-flex !important;
        align-items: center !important;
        gap: 6px !important;
        padding: 3px 10px !important;
        border-radius: 9999px !important;
        font-size: 11.5px !important;
        font-weight: 700 !important;
    }}
    .conclusion-hospital {{
        background: {'rgba(34, 211, 238, 0.15)' if is_dark else 'rgba(0, 127, 158, 0.12)'} !important;
        color: {'#22D3EE' if is_dark else '#007F9E'} !important;
        border: 1px solid {'rgba(34, 211, 238, 0.35)' if is_dark else 'rgba(0, 127, 158, 0.3)'} !important;
    }}
    .conclusion-shelter {{
        background: rgba(168, 85, 247, {'0.18' if is_dark else '0.12'}) !important;
        color: {'#D8B4FE' if is_dark else '#7E22CE'} !important;
        border: 1px solid rgba(168, 85, 247, 0.35) !important;
    }}
    .conclusion-fire {{
        background: {'rgba(251, 191, 36, 0.15)' if is_dark else 'rgba(149, 96, 0, 0.12)'} !important;
        color: {'#FBBF24' if is_dark else '#956000'} !important;
        border: 1px solid {'rgba(251, 191, 36, 0.35)' if is_dark else 'rgba(149, 96, 0, 0.3)'} !important;
    }}
    .conclusion-police {{
        background: {'rgba(34, 211, 238, 0.15)' if is_dark else 'rgba(0, 127, 158, 0.12)'} !important;
        color: {'#22D3EE' if is_dark else '#007F9E'} !important;
        border: 1px solid {'rgba(34, 211, 238, 0.35)' if is_dark else 'rgba(0, 127, 158, 0.3)'} !important;
    }}
    .conclusion-legal {{
        background: rgba(100, 116, 139, {'0.18' if is_dark else '0.12'}) !important;
        color: {'#CBD5E1' if is_dark else '#475569'} !important;
        border: 1px solid rgba(100, 116, 139, 0.35) !important;
    }}

    /* ==========================================================================
       MOBILE RESPONSIVENESS & TOUCH OPTIMIZATIONS (Smartphones & Small Tablets)
       ========================================================================== */
    @media screen and (max-width: 768px) {{
        /* Container and Spacing */
        .main .block-container {{
            padding: 1rem 0.65rem 4rem 0.65rem !important;
            max-width: 100% !important;
        }}

        /* Top Enterprise App-Bar */
        .sahaay-header {{
            flex-direction: column !important;
            align-items: flex-start !important;
            gap: 12px !important;
            padding: 12px 14px !important;
            border-radius: 10px !important;
            margin-bottom: 14px !important;
        }}
        .sahaay-header > div:last-child {{
            width: 100% !important;
            display: flex !important;
            flex-wrap: wrap !important;
            justify-content: space-between !important;
            gap: 8px !important;
        }}
        .sahaay-brand-title {{
            gap: 10px !important;
        }}
        .sahaay-brand-name {{
            font-size: 16px !important;
        }}
        .sahaay-tagline {{
            font-size: 10.5px !important;
            line-height: 1.3 !important;
        }}
        .system-status-capsule {{
            font-size: 11px !important;
            padding: 4px 10px !important;
        }}
        .operator-profile-pill {{
            font-size: 11px !important;
            padding: 4px 10px !important;
        }}

        /* Floating Theme Toggle on Mobile */
        div.st-key-top_right_theme_toggle,
        div[class*="st-key-top_right_theme_toggle"],
        div[data-testid="stElementContainer"]:has(button[key="top_right_theme_toggle"]) {{
            top: 10px !important;
            right: 12px !important;
            width: 36px !important;
            height: 36px !important;
            min-width: 36px !important;
            min-height: 36px !important;
        }}
        div.st-key-top_right_theme_toggle button,
        button[key="top_right_theme_toggle"] {{
            width: 36px !important;
            height: 36px !important;
            min-width: 36px !important;
            min-height: 36px !important;
            font-size: 14px !important;
        }}

        /* Horizontal Column Layouts: Auto-wrap on mobile */
        [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
            gap: 0.75rem !important;
        }}
        [data-testid="stHorizontalBlock"] > [data-testid="column"] {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}

        /* Responsive Metric Grids */
        .grid, [data-testid="stMetric"] {{
            min-width: 100% !important;
        }}
        .grid {{
            grid-template-columns: 1fr 1fr !important;
            gap: 10px !important;
        }}

        /* CAD Cards & Triage Cards */
        .cad-card, .triage-card, .evidence-card, .summary-card {{
            padding: 12px 14px !important;
            margin-bottom: 12px !important;
            border-radius: 8px !important;
        }}

        /* Touch-Friendly Form Controls & Buttons */
        button, .stButton > button {{
            min-height: 44px !important;
            font-size: 13.5px !important;
            padding: 8px 14px !important;
            touch-action: manipulation !important;
        }}

        /* Inputs & Select Boxes */
        input, select, textarea, .stTextInput > div > div > input {{
            font-size: 14px !important;
            min-height: 42px !important;
        }}

        /* Tables and Telemetry Data: Horizontal scrollable */
        div[data-testid="stTable"], .stDataFrame, table {{
            display: block !important;
            width: 100% !important;
            overflow-x: auto !important;
            -webkit-overflow-scrolling: touch !important;
        }}

        /* Softphone Call Bar */
        .call-active-bar, .incoming-call-box {{
            padding: 10px 12px !important;
            font-size: 12px !important;
        }}

        /* Badges & Chips */
        .badge-p0, .badge-p1, .badge-p2, .badge-p3 {{
            font-size: 11px !important;
            padding: 3px 8px !important;
        }}
    }}

    @media screen and (max-width: 480px) {{
        .sahaay-brand-title img {{
            height: 30px !important;
        }}
        .sahaay-brand-name {{
            font-size: 15px !important;
        }}
        .grid {{
            grid-template-columns: 1fr !important;
        }}
        .system-status-capsule span:nth-child(3),
        .system-status-capsule span:nth-child(4) {{
            display: none !important;
        }}
        .operator-profile-pill div:last-child span:last-child {{
            display: none !important;
        }}
    }}

    /* Custom Theme Rules for Dark vs Light Elements */
    {theme_specific_styles}

    </style>
    """
