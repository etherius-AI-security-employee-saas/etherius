from __future__ import annotations

from datetime import datetime, timedelta
from io import BytesIO
from typing import Dict

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.alert import Alert
from app.models.blocked_ip import BlockedIP
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.rbac import require_min_role

router = APIRouter(prefix="/api/dashboard/reports", tags=["Reports"])


def _date_window(days: int):
    now = datetime.utcnow()
    start = now - timedelta(days=max(1, min(days, 365)))
    return start, now


def _security_summary(db: Session, company_id: str, days: int = 30) -> Dict:
    start, end = _date_window(days)

    alerts = db.query(Alert).filter(Alert.company_id == company_id, Alert.created_at >= start, Alert.created_at <= end)
    critical = alerts.filter(Alert.severity == "critical").count()
    high = alerts.filter(Alert.severity == "high").count()
    medium = alerts.filter(Alert.severity == "medium").count()
    low = alerts.filter(Alert.severity.in_(["low", "info"])).count()
    total_alerts = critical + high + medium + low

    endpoints = db.query(Endpoint).filter(Endpoint.company_id == company_id).all()
    top_risky = sorted(
        [{"endpoint_id": ep.id, "hostname": ep.hostname, "risk_score": int(ep.risk_score or 0)} for ep in endpoints],
        key=lambda x: x["risk_score"],
        reverse=True,
    )[:10]

    policy_violations = db.query(Event).filter(
        Event.company_id == company_id,
        Event.created_at >= start,
        Event.created_at <= end,
        Event.event_type.in_(["usb", "dlp", "web", "app_blacklist"]),
    ).count()

    blocked_threats = db.query(BlockedIP).filter(
        BlockedIP.company_id == company_id,
        BlockedIP.is_active == True,
    ).count()

    weighted_alert_impact = critical * 10 + high * 6 + medium * 3 + low * 1
    compliance_score = max(0, min(100, 100 - weighted_alert_impact - min(policy_violations * 2, 30)))

    timeline_rows = (
        db.query(func.date(Event.created_at).label("d"), func.count(Event.id).label("count"))
        .filter(Event.company_id == company_id, Event.created_at >= start, Event.created_at <= end)
        .group_by(func.date(Event.created_at))
        .order_by(func.date(Event.created_at))
        .all()
    )
    alerts_over_time = [{"date": str(row.d), "count": int(row.count)} for row in timeline_rows]

    top_threats_rows = (
        db.query(Event.event_type, func.count(Event.id).label("count"))
        .filter(Event.company_id == company_id, Event.created_at >= start, Event.created_at <= end)
        .group_by(Event.event_type)
        .order_by(desc("count"))
        .limit(8)
        .all()
    )
    top_threats = [{"event_type": row.event_type, "count": int(row.count)} for row in top_threats_rows]

    return {
        "period": {"from": start.isoformat(), "to": end.isoformat(), "days": days},
        "alerts_by_severity": {"critical": critical, "high": high, "medium": medium, "low_or_info": low, "total": total_alerts},
        "top_risky_endpoints": top_risky,
        "policy_violations": policy_violations,
        "blocked_threats_count": blocked_threats,
        "compliance_score": compliance_score,
        "alerts_over_time": alerts_over_time,
        "top_threats": top_threats,
    }


def _escape_pdf_text(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def _simple_pdf(lines):
    text_commands = ["BT", "/F1 11 Tf", "40 800 Td", "14 TL"]
    for line in lines:
        safe = _escape_pdf_text(line[:120])
        text_commands.append(f"({safe}) Tj")
        text_commands.append("T*")
    text_commands.append("ET")
    content = "\n".join(text_commands).encode("latin-1", errors="replace")

    objects = []
    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>")
    objects.append(b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 842] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>")
    objects.append(b"<< /Length " + str(len(content)).encode("ascii") + b" >>\nstream\n" + content + b"\nendstream")
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")

    out = BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = [0]
    for idx, obj in enumerate(objects, start=1):
        offsets.append(out.tell())
        out.write(f"{idx} 0 obj\n".encode("ascii"))
        out.write(obj)
        out.write(b"\nendobj\n")
    xref_start = out.tell()
    out.write(f"xref\n0 {len(objects)+1}\n".encode("ascii"))
    out.write(b"0000000000 65535 f \n")
    for off in offsets[1:]:
        out.write(f"{off:010} 00000 n \n".encode("ascii"))
    out.write(b"trailer\n")
    out.write(f"<< /Size {len(objects)+1} /Root 1 0 R >>\n".encode("ascii"))
    out.write(b"startxref\n")
    out.write(f"{xref_start}\n".encode("ascii"))
    out.write(b"%%EOF")
    out.seek(0)
    return out


@router.get("/security-summary")
def security_summary(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    require_min_role("manager")(u)
    return _security_summary(db, u.company_id, days)


@router.get("/export-pdf")
def export_pdf(
    days: int = Query(30, ge=1, le=365),
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    require_min_role("manager")(u)
    summary = _security_summary(db, u.company_id, days)
    lines = [
        "Etherius Security Summary Report",
        f"Generated: {datetime.utcnow().isoformat()} UTC",
        f"Window: Last {days} day(s)",
        "",
        f"Compliance Score: {summary['compliance_score']}/100",
        f"Blocked Threats: {summary['blocked_threats_count']}",
        f"Policy Violations: {summary['policy_violations']}",
        "",
        "Alerts by Severity:",
        f"  Critical: {summary['alerts_by_severity']['critical']}",
        f"  High: {summary['alerts_by_severity']['high']}",
        f"  Medium: {summary['alerts_by_severity']['medium']}",
        f"  Low/Info: {summary['alerts_by_severity']['low_or_info']}",
        "",
        "Top Risky Endpoints:",
    ]
    for item in summary["top_risky_endpoints"][:8]:
        lines.append(f"  {item['hostname']} ({item['endpoint_id']}): {item['risk_score']}")

    pdf_stream = _simple_pdf(lines)
    filename = f"etherius-security-summary-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.pdf"
    return StreamingResponse(
        pdf_stream,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
