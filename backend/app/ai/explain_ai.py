from typing import Dict
from app.config import settings

def generate_explanation(event_type: str, risk: Dict, hostname: str = "unknown") -> str:
    flags = risk.get("flags", [])
    severity = risk.get("severity", "medium")
    score = risk.get("risk_score", 0)

    if settings.ANTHROPIC_API_KEY:
        try:
            return _ai_explain(event_type, risk, hostname)
        except Exception:
            pass

    lines = [
        f"Security alert on endpoint '{hostname}'.",
        f"Event: {event_type.upper()} | Severity: {severity.upper()} | Risk Score: {score}/100",
    ]
    if flags:
        lines.append("Detected threats:")
        for f in flags: lines.append(f"  • {f}")
    action = {
        "critical": "IMMEDIATE ACTION: Isolate endpoint now.",
        "high": "Investigate this endpoint urgently.",
        "medium": "Review and monitor this endpoint.",
        "low": "Log for monitoring. No immediate action.",
        "info": "Informational only."
    }.get(severity, "Review the event.")
    lines.append(f"Recommended: {action}")
    return "\n".join(lines)

def _ai_explain(event_type: str, risk: Dict, hostname: str) -> str:
    import anthropic
    client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=300,
        messages=[{"role":"user","content":
            f"You are a cybersecurity analyst. Briefly explain this alert for an IT manager.\n"
            f"Endpoint: {hostname} | Event: {event_type} | Score: {risk.get('risk_score')}/100 | "
            f"Severity: {risk.get('severity')} | Flags: {', '.join(risk.get('flags',[]))}\n"
            f"Give: 1) What happened 2) Why risky 3) Action. Be concise."
        }]
    )
    return msg.content[0].text
