from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List


def _safe_int(value, default=0):
    try:
        return int(value)
    except Exception:
        return default


def calculate_insider_threat_score(event_rows: List[Dict], previous_score: int = 0) -> Dict:
    now = datetime.utcnow()
    score = 0
    factors = []

    after_hours = 0
    usb_events = 0
    large_transfer_events = 0
    failed_logins = 0
    unusual_process = 0
    web_violations = 0

    for row in event_rows:
        event_type = str(row.get("event_type", "")).lower()
        payload = row.get("payload", {}) or {}
        created_at = row.get("created_at")
        risk_score = _safe_int(row.get("risk_score"), 0)
        hour_of_day = _safe_int(payload.get("hour_of_day"), 12)
        if created_at and isinstance(created_at, datetime) and created_at < now - timedelta(days=7):
            continue

        if event_type in {"employee_login", "employee_logout", "session_heartbeat"} and (hour_of_day < 6 or hour_of_day > 22):
            after_hours += 1
        if event_type == "usb":
            usb_events += 1
        if event_type in {"network", "dlp"} and _safe_int(payload.get("bytes_sent", 0)) > 50_000_000:
            large_transfer_events += 1
        if event_type in {"login", "employee_login", "session_heartbeat"}:
            failed_logins += _safe_int(payload.get("failed_attempts", 0))
        if event_type == "process" and risk_score >= 45:
            unusual_process += 1
        if event_type == "web":
            web_violations += 1

    if after_hours:
        added = min(after_hours * 4, 20)
        score += added
        factors.append(f"After-hours access frequency elevated (+{added})")
    if usb_events:
        added = min(usb_events * 3, 18)
        score += added
        factors.append(f"USB activity pattern notable (+{added})")
    if large_transfer_events:
        added = min(large_transfer_events * 10, 30)
        score += added
        factors.append(f"Large transfer or exfiltration behavior detected (+{added})")
    if failed_logins:
        added = min(failed_logins * 2, 20)
        score += added
        factors.append(f"Failed login attempts increased (+{added})")
    if unusual_process:
        added = min(unusual_process * 5, 25)
        score += added
        factors.append(f"Unusual process execution frequency increased (+{added})")
    if web_violations:
        added = min(web_violations * 4, 16)
        score += added
        factors.append(f"Website policy violations observed (+{added})")

    score = max(0, min(100, score))
    trend = "stable"
    if score - previous_score >= 8:
        trend = "rising"
    elif previous_score - score >= 8:
        trend = "falling"

    if not factors:
        factors = ["No significant insider threat indicators in the last 7 days."]

    return {"score": score, "trend": trend, "factors": factors}
