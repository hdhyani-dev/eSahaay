"""Role-based access control and authorization matrix."""
from typing import Set, Dict, Any

ROLES = {
    "operator": "Call-taker / Operator",
    "supervisor": "Shift Supervisor",
    "responder": "Responder Agency Liaison",
    "linguist": "Helpline Linguist / Curator",
    "admin": "System Administrator",
    "judge": "Judge / Evaluator (Demo View)"
}

# Permission matrix matching PRD Section 2.2
PERMISSIONS: Dict[str, Set[str]] = {
    "operator": {
        "view_live_queue",
        "confirm_override_urgency",
        "see_raw_transcript",
        "suggest_repeat_links",
        "assign_dispatch",
        "view_case_detail",
        "use_simulator"
    },
    "supervisor": {
        "view_live_queue",
        "confirm_override_urgency",
        "see_raw_transcript",
        "approve_undo_repeat_links",
        "propose_lexicon",
        "view_case_detail",
        "view_eval_dashboard",
        "view_impact_board",
        "export_audit_log",
        "use_simulator"
    },
    "responder": {
        "view_assigned_dispatches",
        "acknowledge_dispatch",
        "update_unit_status",
        "see_masked_transcript"
    },
    "linguist": {
        "view_lexicon",
        "edit_lexicon",
        "test_simulator",
        "see_masked_sample"
    },
    "admin": {
        "view_live_queue",
        "see_raw_transcript_audited",
        "approve_undo_repeat_links",
        "approve_lexicon",
        "change_thresholds_models",
        "export_audit_log",
        "manage_users",
        "view_eval_dashboard",
        "view_impact_board",
        "use_simulator"
    },
    "judge": {
        "view_live_queue",
        "view_eval_dashboard",
        "use_simulator",
        "view_impact_board",
        "export_hidden_predictions"
    }
}

def has_permission(role: str, permission: str) -> bool:
    """Verify if a given role has the requested capability."""
    role_perms = PERMISSIONS.get(role.lower(), set())
    return permission in role_perms

def can_access_page(role: str, page_name: str) -> bool:
    """Determine if a role can view a given navigation page."""
    role = role.lower()
    page_role_map = {
        "home": ["operator", "supervisor", "responder", "linguist", "admin", "judge"],
        "ps3": ["operator", "supervisor", "responder", "linguist", "admin", "judge"],
        "ps3_landing": ["operator", "supervisor", "responder", "linguist", "admin", "judge"],
        "dashboard": ["operator", "supervisor", "admin", "judge"],
        "triage": ["operator", "supervisor", "admin"],
        "case_detail": ["operator", "supervisor", "admin"],
        "location_recovery": ["operator", "supervisor", "admin"],
        "dispatch": ["operator", "supervisor", "responder", "admin"],
        "map_view": ["operator", "supervisor", "responder", "admin", "judge"],
        "incidents": ["operator", "supervisor", "admin", "judge", "responder"],
        "repeats": ["operator", "supervisor", "admin", "judge"],
        "repeat_review": ["operator", "supervisor", "admin", "judge"],
        "lexicon": ["linguist", "admin", "supervisor"],
        "simulator": ["operator", "supervisor", "linguist", "admin", "judge"],
        "eval": ["supervisor", "admin", "judge"],
        "impact": ["operator", "supervisor", "responder", "linguist", "admin", "judge"],
        "admin": ["admin"],
        "help": ["operator", "supervisor", "responder", "linguist", "admin", "judge"]
    }
    allowed = page_role_map.get(page_name.lower(), ["operator", "admin"])
    return role in allowed
