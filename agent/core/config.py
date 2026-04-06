import json
import sys
from pathlib import Path


DEFAULT_CONFIG = {
    "backend_url": "https://etherius-security-api.vercel.app",
    "company_code": "",
    "employee_key": "",
    "activation_code": "",
    "agent_token": "PASTE_YOUR_AGENT_TOKEN_HERE",
    "endpoint_id": "PASTE_YOUR_ENDPOINT_ID_HERE",
    "heartbeat_interval": 30,
    "event_batch_interval": 10,
    "policy_mode": "advisory",
    "ai_profile": "balanced",
    "ai_sensitivity": 70,
    "non_disruptive_mode": True,
    "enforcement_threshold": 84,
    "block_during_business_hours": False,
    "business_hours_start": "08:00",
    "business_hours_end": "20:00",
    "trusted_processes": [
        "outlook.exe",
        "teams.exe",
        "slack.exe",
        "zoom.exe",
        "chrome.exe",
        "msedge.exe",
        "firefox.exe",
        "code.exe",
    ],
    "trusted_domains": [
        "microsoft.com",
        "office.com",
        "google.com",
        "github.com",
        "zoom.us",
        "slack.com",
    ],
    "trusted_download_patterns": [],
    "web_control_enforce": False,
    "download_shield_enabled": True,
    "download_shield_quarantine": True,
    "exploit_guard_enabled": True,
    "exploit_guard_auto_kill": True,
    "beacon_guard_enabled": True,
    "beacon_guard_block": False,
    "version": "1.2.0",
}


def _resolve_config_file() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent / "agent_config.json"
    return Path(__file__).resolve().parents[1] / "agent_config.json"


CONFIG_FILE = _resolve_config_file()


def load_config():
    if not CONFIG_FILE.exists():
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception:
        save_config(DEFAULT_CONFIG.copy())
        return DEFAULT_CONFIG.copy()

    merged = DEFAULT_CONFIG.copy()
    merged.update(data if isinstance(data, dict) else {})
    return merged


def save_config(cfg):
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


config = load_config()


def get_config():
    global config
    config = load_config()
    return config


def update_config(partial):
    current = get_config()
    current.update(partial)
    save_config(current)
    return get_config()
