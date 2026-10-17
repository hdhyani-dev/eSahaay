"""Configuration manager for eSahaay application and policy settings."""
import os
import yaml
from pathlib import Path
from typing import Any, Dict

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIG_DIR = BASE_DIR / "config"

def _load_yaml(file_path: Path) -> Dict[str, Any]:
    if file_path.exists():
        with open(file_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}

def _resolve_sqlite_url(configured_url: str) -> str:
    """Resolve sqlite URL to a reliably writable path."""
    if not configured_url.startswith("sqlite:"):
        return configured_url
    
    # Try local workspace path first
    local_path = BASE_DIR / "sahaay.db"
    try:
        import sqlite3
        conn = sqlite3.connect(str(local_path))
        conn.execute("CREATE TABLE IF NOT EXISTS _perm_check (id INT)")
        conn.execute("DROP TABLE _perm_check")
        conn.close()
        return f"sqlite:///{local_path.as_posix()}"
    except Exception:
        # Fall back to user home directory ~/.sahaay
        home_db_dir = Path.home() / ".sahaay"
        home_db_dir.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{(home_db_dir / 'sahaay.db').as_posix()}"

class Settings:
    def __init__(self):
        self.app_config = _load_yaml(CONFIG_DIR / "app.yaml")
        self.policy_config = _load_yaml(CONFIG_DIR / "policy.yaml")
        
        # Database
        env_db = os.environ.get(self.app_config.get("database", {}).get("postgres_url_env", "DATABASE_URL"))
        if env_db:
            self.database_url = env_db
        else:
            cfg_db = self.app_config.get("database", {}).get("sqlite_url", "sqlite:///sahaay.db")
            self.database_url = _resolve_sqlite_url(cfg_db)

        # HMAC & Security
        self.hmac_secret = os.environ.get(
            self.app_config.get("security", {}).get("hmac_secret_key_env", "SAHAAY_HMAC_KEY"),
            self.app_config.get("security", {}).get("default_hmac_key", "sahaay-emergency-triage-hmac-salt-2026-bvp")
        )
        self.bcrypt_rounds = self.app_config.get("security", {}).get("bcrypt_rounds", 12)
        
        # Policy & Triage
        self.confidence_tau = float(self.policy_config.get("urgency", {}).get("confidence_threshold_tau", 0.70))
        self.short_call_word_threshold = int(self.policy_config.get("urgency", {}).get("short_call_word_threshold", 12))
        self.cost_matrix = self.policy_config.get("urgency", {}).get("cost_matrix", {
            "P0": {"P0": 0, "P1": 5, "P2": 25, "P3": 60},
            "P1": {"P0": 1, "P1": 0, "P2": 5, "P3": 25},
            "P2": {"P0": 2, "P1": 1, "P2": 0, "P3": 5},
            "P3": {"P0": 3, "P1": 2, "P2": 1, "P3": 0}
        })
        self.escalation_rules = self.policy_config.get("urgency", {}).get("escalation_rules", {})
        self.threat_routing_matrix = self.policy_config.get("routing", {}).get("threat_routing_matrix", {})
        
        # AI Provider
        self.ai_provider = os.environ.get("SAHAAY_AI_PROVIDER", self.app_config.get("ai_pipeline", {}).get("provider", "hybrid"))
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY", "")
        self.openai_api_key = os.environ.get("OPENAI_API_KEY", "")
        
        # Dispatch Simulation
        self.sim_speed_kmh = float(self.app_config.get("dispatch_simulation", {}).get("speed_kmh", 40.0))
        self.center_lat = float(self.app_config.get("dispatch_simulation", {}).get("center_lat", 28.6139))
        self.center_lon = float(self.app_config.get("dispatch_simulation", {}).get("center_lon", 77.2090))

settings = Settings()
