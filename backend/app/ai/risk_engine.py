from typing import Dict, Any, Optional
from app.ai.behavior_ai import analyze_event
from app.ai.anomaly_ai import score_anomaly
from app.ai.decision_engine import evaluate_decision

def get_severity(score: int) -> str:
    if score >= 80: return "critical"
    if score >= 60: return "high"
    if score >= 40: return "medium"
    if score >= 20: return "low"
    return "info"

def calculate_risk(event_type: str, payload: Dict, baseline: Optional[Dict] = None, context: Optional[Dict] = None) -> Dict:
    behavior = analyze_event(event_type, payload)
    anomaly = score_anomaly(event_type, payload, baseline)
    b_score = behavior.get("score", 0)
    a_score = anomaly.get("anomaly_score", 0)
    combined = min(int(b_score * 0.7 + a_score * 0.3), 100)
    flags = behavior.get("flags", [])
    parts = []
    if flags: parts.append("Behavioral: " + ", ".join(flags))
    if anomaly.get("reason","Normal") != "Normal": parts.append("Anomaly: " + anomaly["reason"])
    base_explanation = ". ".join(parts) or "No significant threat."

    decision_result = evaluate_decision(
        event_type=event_type,
        payload=payload,
        flags=flags,
        base_explanation=base_explanation,
        endpoint_id=str((context or {}).get("endpoint_id", "unknown")),
        signals={
            "behavior_score": b_score,
            "anomaly_score": a_score,
            "insider_threat_score": payload.get("insider_threat_score", 0),
            "dlp_score": payload.get("dlp_score", b_score if event_type == "dlp" else 0),
            "usb_score": payload.get("usb_score", b_score if event_type == "usb" else 0),
        },
    )

    return {
        "risk_score": decision_result["risk_score"], "severity": decision_result["severity"],
        "should_alert": decision_result["should_alert"],
        "flags": flags, "behavior_score": b_score,
        "anomaly_score": a_score,
        "decision": decision_result["decision"],
        "recommended_actions": decision_result["recommended_actions"],
        "decision_factors": decision_result["decision_factors"],
        "base_risk_score": combined,
        "explanation": decision_result["explanation"],
    }

def build_alert_title(event_type: str, flags: list, severity: str) -> str:
    if flags: return f"[{severity.upper()}] {flags[0]}"
    return f"[{severity.upper()}] Suspicious {event_type} activity"
