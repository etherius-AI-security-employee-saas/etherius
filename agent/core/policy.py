import threading
import time

from agent.core.client import get_policies


_LOCK = threading.Lock()
_CACHE = {
    "usb_policy": "allow_all",
    "usb_whitelist": [],
    "app_blacklist": [],
    "blocked_domains": [],
    "_fetched_at": 0.0,
}


def refresh_policies(force=False):
    now = time.time()
    with _LOCK:
        if not force and now - _CACHE.get("_fetched_at", 0) < 20:
            return dict(_CACHE)
    try:
        response = get_policies(timeout=10)
        response.raise_for_status()
        data = response.json() or {}
        with _LOCK:
            _CACHE["usb_policy"] = data.get("usb_policy", "allow_all")
            _CACHE["usb_whitelist"] = data.get("usb_whitelist", [])
            _CACHE["app_blacklist"] = data.get("app_blacklist", [])
            _CACHE["blocked_domains"] = data.get("blocked_domains", [])
            _CACHE["_fetched_at"] = now
    except Exception:
        pass
    with _LOCK:
        return dict(_CACHE)


def get_policy_snapshot():
    return refresh_policies(force=False)
