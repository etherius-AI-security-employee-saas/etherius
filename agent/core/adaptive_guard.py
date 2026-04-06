from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, List


def _safe_bool(value: Any, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except Exception:
        return default


def _normalize_name(name: str) -> str:
    text = str(name or "").strip().lower()
    if not text:
        return ""
    return Path(text).name


def _parse_list(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        raw = list(value)
    else:
        raw = str(value).replace(";", ",").split(",")
    return [str(item).strip().lower() for item in raw if str(item).strip()]


def _in_business_hours(cfg: dict) -> bool:
    start = str(cfg.get("business_hours_start", "08:00")).strip()
    end = str(cfg.get("business_hours_end", "20:00")).strip()

    def _minutes(text: str) -> int:
        try:
            hh, mm = text.split(":")
            return int(hh) * 60 + int(mm)
        except Exception:
            return 0

    now = datetime.now()
    now_minutes = now.hour * 60 + now.minute
    s = _minutes(start)
    e = _minutes(end)
    if s == e:
        return True
    if s < e:
        return s <= now_minutes <= e
    return now_minutes >= s or now_minutes <= e


def is_process_allowlisted(process_name: str, cfg: dict) -> bool:
    name = _normalize_name(process_name)
    if not name:
        return False
    for allowed in _parse_list(cfg.get("trusted_processes", [])):
        normalized = _normalize_name(allowed)
        if not normalized:
            continue
        if name == normalized:
            return True
        if normalized.endswith(".exe") and name == normalized[:-4]:
            return True
        if name.endswith(".exe") and normalized == f"{name[:-4]}":
            return True
    return False


def is_domain_allowlisted(domain: str, cfg: dict) -> bool:
    host = str(domain or "").strip().lower()
    if not host:
        return False
    for allowed in _parse_list(cfg.get("trusted_domains", [])):
        if host == allowed or host.endswith(f".{allowed}"):
            return True
    return False


def is_path_allowlisted(path_text: str, cfg: dict) -> bool:
    path_l = str(path_text or "").strip().lower()
    if not path_l:
        return False
    for pattern in _parse_list(cfg.get("trusted_download_patterns", [])):
        if pattern and pattern in path_l:
            return True
    return False


def _profile_shift(profile: str) -> int:
    profile_l = str(profile or "balanced").strip().lower()
    if profile_l == "conservative":
        return 8
    if profile_l == "aggressive":
        return -6
    return 0


def should_enforce_action(
    cfg: dict,
    action_kind: str,
    signal_score: int,
    critical: bool = False,
) -> bool:
    policy_mode = str(cfg.get("policy_mode", "advisory")).strip().lower()
    if policy_mode == "advisory":
        return False

    threshold = _safe_int(cfg.get("enforcement_threshold", 84), 84)
    threshold += _profile_shift(cfg.get("ai_profile", "balanced"))

    sensitivity = _safe_int(cfg.get("ai_sensitivity", 70), 70)
    threshold += int((70 - sensitivity) / 5)

    if _safe_bool(cfg.get("non_disruptive_mode", True), True):
        threshold += 6

    action_kind = str(action_kind or "").strip().lower()
    if action_kind in {"terminate_process", "network_block", "hosts_block"}:
        threshold += 5
    elif action_kind == "quarantine_file":
        threshold += 3

    if policy_mode == "strict":
        threshold -= 8
    elif policy_mode == "balanced":
        threshold += 1

    if (
        not _safe_bool(cfg.get("block_during_business_hours", False), False)
        and _in_business_hours(cfg)
        and action_kind in {"terminate_process", "network_block", "hosts_block", "quarantine_file"}
        and not critical
    ):
        threshold += 6

    if critical:
        threshold -= 12

    threshold = max(45, min(95, threshold))
    return int(signal_score) >= threshold


def compute_connection_threshold(cfg: dict, base: int = 14) -> int:
    threshold = int(base)
    threshold += _profile_shift(cfg.get("ai_profile", "balanced")) // 2
    sensitivity = _safe_int(cfg.get("ai_sensitivity", 70), 70)
    threshold += int((70 - sensitivity) / 10)
    if _safe_bool(cfg.get("non_disruptive_mode", True), True):
        threshold += 3
    mode = str(cfg.get("policy_mode", "advisory")).strip().lower()
    if mode == "strict":
        threshold -= 2
    elif mode == "advisory":
        threshold += 2
    return max(8, min(30, threshold))


def csv_from_list(values: Iterable[Any]) -> str:
    clean = [str(v).strip() for v in values if str(v).strip()]
    return ", ".join(clean)
