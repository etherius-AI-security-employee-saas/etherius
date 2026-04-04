from typing import Dict, Any, Optional
from app.ai.behavior_ai import analyze_event
from app.ai.anomaly_ai import score_anomaly

def get_severity(score: int) -> str:
    if score >= 80: return "critical"
    if score >= 60: return "high"
    if score >= 40: return "medium"
    if score >= 20: return "low"
    return "info"

def calculate_risk(event_type: str, payload: Dict, baseline: Optional[Dict] = None) -> Dict:
    behavior = analyze_event(event_type, payload)
    anomaly = score_anomaly(event_type, payload, baseline)
    b_score = behavior.get("score", 0)
    a_score = anomaly.get("anomaly_score", 0)
    combined = min(int(b_score * 0.7 + a_score * 0.3), 100)
    severity = get_severity(combined)
    flags = behavior.get("flags", [])
    parts = []
    if flags: parts.append("Behavioral: " + ", ".join(flags))
    if anomaly.get("reason","Normal") != "Normal": parts.append("Anomaly: " + anomaly["reason"])
    return {
        "risk_score": combined, "severity": severity,
        "should_alert": combined >= 40,
        "flags": flags, "behavior_score": b_score,
        "anomaly_score": a_score,
        "explanation": ". ".join(parts) or "No significant threat."
    }

def build_alert_title(event_type: str, flags: list, severity: str) -> str:
    if flags: return f"[{severity.upper()}] {flags[0]}"
    return f"[{severity.upper()}] Suspicious {event_type} activity"
