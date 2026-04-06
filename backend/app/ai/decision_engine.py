from __future__ import annotations

from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Deque, Dict, List, Tuple


DECISION_MONITOR = "MONITOR"
DECISION_ALERT = "ALERT"
DECISION_AUTO_BLOCK = "AUTO_BLOCK"
DECISION_ISOLATE = "ISOLATE"
DECISION_CRITICAL = "CRITICAL"


_RECENT_EVENTS: Dict[Tuple[str, str], Deque[Dict[str, Any]]] = defaultdict(deque)
_REPEAT_TRACKER: Dict[Tuple[str, str], Dict[str, Any]] = defaultdict(dict)


def _bounded_score(value: Any) -> int:
    try:
        return max(0, min(100, int(float(value or 0))))
    except Exception:
        return 0


def _event_identity(event_type: str, payload: Dict[str, Any]) -> str:
    if event_type == "process":
        return f"{event_type}:{str(payload.get('process_name', '')).lower()}"
    if event_type == "network":
        return f"{event_type}:{payload.get('dest_ip', '')}:{payload.get('dest_port', '')}"
    if event_type == "file":
        return f"{event_type}:{str(payload.get('file_path', '')).lower()}"
    if event_type == "usb":
        return f"{event_type}:{str(payload.get('device_id', '')).lower()}"
    if event_type == "dlp":
        return f"{event_type}:{str(payload.get('pattern_type', '')).lower()}"
    return event_type


def _track_recent(endpoint_id: str, event_type: str, final_score: int):
    key = (endpoint_id, event_type)
    now = datetime.utcnow()
    bucket = _RECENT_EVENTS[key]
    bucket.append({"time": now, "score": final_score})
    while bucket and bucket[0]["time"] < now - timedelta(hours=1):
        bucket.popleft()
    medium_count = sum(1 for item in bucket if item["score"] >= 45)
    return medium_count


def _apply_false_positive_reduction(endpoint_id: str, event_type: str, event_identity: str, final_score: int):
    """
    Reduce severity for repeated, non-escalating signatures over time.
    """
    now = datetime.utcnow()
    key = (endpoint_id, event_identity)
    item = _REPEAT_TRACKER.get(key) or {"last_score": final_score, "count": 0, "seen_at": now}
    last_score = _bounded_score(item.get("last_score"))
    count = int(item.get("count", 0))
    seen_at = item.get("seen_at", now)

    if isinstance(seen_at, datetime) and seen_at < now - timedelta(hours=4):
        count = 0

    if final_score <= last_score:
        count += 1
    else:
        count = 0

    _REPEAT_TRACKER[key] = {"last_score": final_score, "count": count, "seen_at": now}

    reduction = 0
    if count >= 5 and final_score < 80:
        reduction = 15
    elif count >= 3 and final_score < 80:
        reduction = 8
    return max(0, final_score - reduction), reduction, count


def _event_hard_override(event_type: str, payload: Dict[str, Any], flags: List[str]):
    lowered_flags = [str(flag).lower() for flag in flags]
    pattern_type = str(payload.get("pattern_type", "")).lower()
    category = str(payload.get("category", "")).lower()
    action = str(payload.get("action", "")).lower()

    if event_type == "dlp":
        bytes_copied = int(float(payload.get("bytes_copied", 0) or 0))
        matches = _bounded_score(payload.get("matches", 0))
        critical_pattern = any(token in pattern_type for token in ["api_key", "credit_card", "ssn", "password", "secret", "token"])
        mass_copy = "mass_copy" in pattern_type or bytes_copied >= 100_000_000
        if mass_copy or matches >= 8:
            return DECISION_AUTO_BLOCK, 86, "Critical DLP event detected (mass copy or high sensitive match count)"
        if critical_pattern or bytes_copied >= 25_000_000 or matches >= 1:
            return DECISION_ALERT, 68, "Sensitive data movement detected by DLP policy"

    if event_type == "usb":
        if action == "blocked":
            return DECISION_ALERT, 72, "USB policy blocked device access"
        if action == "plugged" and not bool(payload.get("is_whitelisted", False)):
            return DECISION_ALERT, 62, "Unknown USB device inserted"

    if event_type == "app_blacklist":
        if bool(payload.get("killed", False)):
            return DECISION_AUTO_BLOCK, 82, "Blacklisted application was executed and terminated"
        return DECISION_ALERT, 66, "Blacklisted application execution attempt detected"

    if event_type == "process":
        if action == "exploit_chain_blocked":
            return DECISION_AUTO_BLOCK, 84, "Exploit chain blocked at endpoint runtime"
        if action == "exploit_chain_detected":
            return DECISION_ALERT, 70, "Exploit chain behavior detected from user application"

    if event_type == "file":
        if action == "quarantine":
            return DECISION_AUTO_BLOCK, 84, "Suspicious file quarantined before execution"
        if action == "suspicious_download_detected":
            return DECISION_ALERT, 64, "Suspicious download detected"

    if event_type == "network" and action == "beacon_pattern_detected":
        if bool(payload.get("local_blocked", False)):
            return DECISION_AUTO_BLOCK, 82, "Beaconing endpoint traffic detected and locally blocked"
        return DECISION_AUTO_BLOCK, 74, "Beaconing endpoint traffic detected"

    if event_type == "web" and bool(payload.get("blocked", False)):
        if category in {"adult", "gambling"}:
            return DECISION_ALERT, 60, "Blocked high-risk website category visited"
        return DECISION_ALERT, 50, "Blocked website policy violation detected"

    if event_type == "vulnerability":
        critical_count = _bounded_score(payload.get("critical_count", 0))
        high_count = _bounded_score(payload.get("high_count", 0))
        if critical_count >= 3:
            return DECISION_ISOLATE, 82, "Multiple critical vulnerabilities require immediate remediation"
        if critical_count > 0 or high_count >= 3:
            return DECISION_ALERT, 62, "Endpoint vulnerability exposure above policy threshold"

    if any("ransomware indicator" in flag for flag in lowered_flags):
        return DECISION_CRITICAL, 95, "Ransomware indicator detected"

    return None, 0, ""


def evaluate_decision(
    event_type: str,
    payload: Dict[str, Any],
    signals: Dict[str, Any],
    flags: List[str],
    base_explanation: str,
    endpoint_id: str = "unknown",
) -> Dict[str, Any]:
    behavior_score = _bounded_score(signals.get("behavior_score"))
    anomaly_score = _bounded_score(signals.get("anomaly_score"))
    insider_threat_score = _bounded_score(signals.get("insider_threat_score"))
    dlp_score = _bounded_score(signals.get("dlp_score"))
    usb_score = _bounded_score(signals.get("usb_score"))

    weighted_score = (
        behavior_score * 0.45
        + anomaly_score * 0.20
        + insider_threat_score * 0.20
        + dlp_score * 0.10
        + usb_score * 0.05
    )
    final_score = _bounded_score(weighted_score)

    reasons: List[str] = []
    decision, forced_score, forced_reason = _event_hard_override(event_type, payload, flags)
    hard_signal_enforced = bool(decision)

    if hard_signal_enforced:
        final_score = max(final_score, forced_score)
        reasons.append(forced_reason)
    elif final_score >= 80:
        decision = DECISION_ISOLATE
        reasons.append("Critical weighted score (80+)")
    elif final_score >= 60:
        decision = DECISION_AUTO_BLOCK
        reasons.append("High weighted score (60+)")
    elif final_score >= 40:
        decision = DECISION_ALERT
        reasons.append("Single medium/high suspicious event")
    else:
        decision = DECISION_MONITOR
        reasons.append("Low risk, monitor only")

    medium_cluster = _track_recent(endpoint_id, event_type, final_score)
    if medium_cluster >= 3 and decision in {DECISION_MONITOR, DECISION_ALERT} and not hard_signal_enforced:
        decision = DECISION_AUTO_BLOCK
        final_score = max(final_score, 65)
        reasons.append("Multiple medium events in rolling 1 hour window")

    event_identity = _event_identity(event_type, payload)
    if not hard_signal_enforced:
        adjusted_score, reduction, repeat_count = _apply_false_positive_reduction(
            endpoint_id=endpoint_id,
            event_type=event_type,
            event_identity=event_identity,
            final_score=final_score,
        )
        if reduction > 0:
            final_score = adjusted_score
            reasons.append(f"False-positive reduction applied ({reduction} points, repeat count {repeat_count})")
            if final_score < 40 and decision != DECISION_CRITICAL:
                decision = DECISION_MONITOR
            elif final_score < 60 and decision in {DECISION_AUTO_BLOCK, DECISION_ISOLATE}:
                decision = DECISION_ALERT

    severity = "info"
    if final_score >= 80:
        severity = "critical"
    elif final_score >= 60:
        severity = "high"
    elif final_score >= 40:
        severity = "medium"
    elif final_score >= 20:
        severity = "low"

    if decision == DECISION_CRITICAL:
        severity = "critical"
    elif decision == DECISION_ISOLATE:
        severity = "high" if severity in {"low", "info"} else severity
    elif decision == DECISION_AUTO_BLOCK:
        severity = "high" if final_score >= 55 else "medium"

    recommended_actions = []
    if decision == DECISION_MONITOR:
        recommended_actions = ["log_event", "continue_monitoring"]
    elif decision == DECISION_ALERT:
        recommended_actions = ["create_alert", "notify_admin"]
    elif decision == DECISION_AUTO_BLOCK:
        recommended_actions = ["create_alert", "notify_admin", "auto_block_ip"]
    elif decision == DECISION_ISOLATE:
        recommended_actions = ["create_alert", "notify_admin", "recommend_isolation"]
    elif decision == DECISION_CRITICAL:
        recommended_actions = [
            "create_alert",
            "notify_admin",
            "auto_block_ip",
            "recommend_isolation",
            "trigger_incident_mode",
        ]

    signal_summary = (
        f"Signals - behavior:{behavior_score}, anomaly:{anomaly_score}, "
        f"insider:{insider_threat_score}, dlp:{dlp_score}, usb:{usb_score}"
    )
    explanation_parts = [base_explanation, signal_summary, "Decision factors: " + "; ".join(reasons)]
    explanation = ". ".join([part for part in explanation_parts if part]).strip()

    return {
        "decision": decision,
        "severity": severity,
        "risk_score": final_score,
        "should_alert": decision in {DECISION_ALERT, DECISION_AUTO_BLOCK, DECISION_ISOLATE, DECISION_CRITICAL},
        "recommended_actions": recommended_actions,
        "explanation": explanation,
        "decision_factors": reasons,
    }
