from typing import Dict, Any, Optional
from datetime import datetime

def score_anomaly(event_type: str, payload: Dict, baseline: Optional[Dict] = None) -> Dict:
    if not baseline:
        return {"anomaly_score": 0, "reason": "No baseline"}
    score, reasons = 0, []
    hour = datetime.utcnow().hour
    typical = baseline.get("typical_hours", list(range(8,18)))
    if hour not in typical:
        score += 25; reasons.append(f"Unusual hour: {hour}:00")
    if event_type == "network":
        avg = baseline.get("avg_bytes", 0)
        curr = payload.get("bytes_sent", 0)
        if avg > 0 and curr > avg * 3:
            score += 40; reasons.append("Network volume 3x above baseline")
    if event_type == "process":
        known = baseline.get("known_processes", [])
        proc = payload.get("process_name","").lower()
        if known and proc not in known:
            score += 20; reasons.append(f"New process: {proc}")
    return {"anomaly_score": min(score,100), "reason": "; ".join(reasons) or "Normal"}
