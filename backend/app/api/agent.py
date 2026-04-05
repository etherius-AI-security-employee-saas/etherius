from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from app.database import get_db
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.company import Company
from app.models.alert import Alert
from app.models.app_blacklist import AppBlacklist
from app.models.blocked_domain import BlockedDomain
from app.models.agent_command import AgentCommand
from app.models.software_inventory import SoftwareInventory
from app.models.usb_device import UsbDevice
from app.models.usb_policy import UsbPolicy
from app.schemas.endpoint import EndpointEnroll, EndpointRegister
from app.schemas.event import EventSubmit
from app.security.dependencies import get_current_agent, get_current_user
from app.security.enrollment import parse_company_code
from app.security.jwt_handler import create_agent_token
from app.security.licenses import validate_employee_key
from app.security.rbac import require_min_role
from app.security.subscription_guard import has_active_company_subscription
from app.ai.risk_engine import calculate_risk, build_alert_title
from app.ai.explain_ai import generate_explanation
from app.ai.decision_engine import DECISION_AUTO_BLOCK, DECISION_CRITICAL, DECISION_ISOLATE
from app.security.ip_blocker import block_ip as auto_block_ip
from app.utils.audit import log_action
from app.config import settings

router = APIRouter(prefix="/api/agent", tags=["Agent"])

_VULN_CATALOG = {
    "google chrome": {"cve_id": "CVE-2025-0001", "severity": "high"},
    "microsoft edge": {"cve_id": "CVE-2025-0002", "severity": "high"},
    "adobe reader": {"cve_id": "CVE-2025-1001", "severity": "critical"},
    "java": {"cve_id": "CVE-2025-1200", "severity": "critical"},
    "winrar": {"cve_id": "CVE-2025-1201", "severity": "high"},
    "7-zip": {"cve_id": "CVE-2025-1202", "severity": "medium"},
}
_DEFAULT_APP_BLACKLIST = [
    ("mimikatz", "kill"),
    ("netcat", "kill"),
    ("nc.exe", "kill"),
    ("qbittorrent", "alert"),
    ("utorrent", "alert"),
    ("tor", "alert"),
]


class CommandResultReq(BaseModel):
    status: str  # executed | failed
    result_text: Optional[str] = ""


class SoftwareItemReq(BaseModel):
    software_name: str
    version: Optional[str] = ""


class SoftwareInventoryReq(BaseModel):
    items: List[SoftwareItemReq]


def _activation_code(endpoint_id: str, token: str) -> str:
    base = (settings.PUBLIC_API_BASE_URL or "http://localhost:8000").strip().rstrip("/")
    return f"{base}|{endpoint_id}|{token}"

@router.post("/register", status_code=201)
def register_endpoint(data: EndpointRegister, db: Session = Depends(get_db),
                      current_user=Depends(get_current_user)):
    require_min_role("manager")(current_user)
    ep = Endpoint(
        company_id=current_user.company_id, hostname=data.hostname,
        os=data.os, ip_address=data.ip_address,
        mac_address=data.mac_address, agent_version=data.agent_version, status="online"
    )
    db.add(ep); db.flush()
    token = create_agent_token(ep.id, current_user.company_id)
    ep.agent_token = token; db.commit()
    log_action(db, current_user.id, current_user.company_id, "REGISTER_ENDPOINT", "endpoint", ep.id)
    activation_code = _activation_code(ep.id, token)
    return {"endpoint_id": ep.id, "agent_token": token,
            "activation_code": activation_code,
            "message": "Endpoint registered. Save agent_token securely."}

@router.post("/enroll", status_code=201)
def enroll_endpoint(data: EndpointEnroll, db: Session = Depends(get_db)):
    company_id = parse_company_code(data.company_code.strip())
    if not company_id:
        raise HTTPException(400, "Invalid company code")
    company = db.query(Company).filter(Company.id == company_id, Company.is_active == True).first()
    if not company:
        raise HTTPException(404, "Company not found")
    if not has_active_company_subscription(db, company_id):
        raise HTTPException(403, "Customer subscription is inactive or expired")

    existing = db.query(Endpoint).filter(
        Endpoint.company_id == company_id,
        Endpoint.hostname == data.hostname,
        Endpoint.mac_address == data.mac_address,
    ).first()

    employee_license = None
    if company.license_enforcement:
        if not data.employee_key:
            raise HTTPException(400, "Employee license key is required for this company")
        employee_license = validate_employee_key(
            db,
            data.employee_key,
            company_id=company_id,
            endpoint_id=existing.id if existing else None,
        )
        if not employee_license:
            raise HTTPException(400, "Invalid, expired, or exhausted employee license key")

    if not existing:
        current_count = db.query(Endpoint).filter(Endpoint.company_id == company_id).count()
        allowed = int(company.max_endpoints or 0)
        if allowed > 0 and current_count >= allowed:
            raise HTTPException(403, f"Seat limit reached ({allowed}). Contact your provider for more employee licenses.")
    if existing:
        token = existing.agent_token or create_agent_token(existing.id, company_id)
        existing.agent_token = token
        existing.status = "online"
        if employee_license and employee_license.used_by_endpoint_id != existing.id:
            employee_license.current_activations += 1
            employee_license.last_used_at = datetime.utcnow()
            employee_license.used_by_endpoint_id = existing.id
        db.commit()
        activation_code = _activation_code(existing.id, token)
        return {
            "endpoint_id": existing.id,
            "agent_token": token,
            "activation_code": activation_code,
            "message": "Endpoint re-enrolled successfully.",
        }
    ep = Endpoint(
        company_id=company_id,
        hostname=data.hostname,
        os=data.os,
        ip_address=data.ip_address,
        mac_address=data.mac_address,
        agent_version=data.agent_version,
        status="online",
    )
    db.add(ep)
    db.flush()
    token = create_agent_token(ep.id, company_id)
    ep.agent_token = token
    if employee_license and employee_license.used_by_endpoint_id != ep.id:
        employee_license.current_activations += 1
        employee_license.last_used_at = datetime.utcnow()
        employee_license.used_by_endpoint_id = ep.id
    db.commit()
    activation_code = _activation_code(ep.id, token)
    return {
        "endpoint_id": ep.id,
        "agent_token": token,
        "activation_code": activation_code,
        "message": "Endpoint enrolled successfully.",
    }

@router.post("/heartbeat")
def heartbeat(db: Session = Depends(get_db), endpoint: Endpoint = Depends(get_current_agent)):
    endpoint.last_seen = datetime.utcnow(); endpoint.status = "online"; db.commit()
    return {"status": "ok", "endpoint_id": endpoint.id}

@router.post("/event")
def submit_event(data: EventSubmit, db: Session = Depends(get_db),
                 endpoint: Endpoint = Depends(get_current_agent)):
    if data.event_type == "usb":
        policy = db.query(UsbPolicy).filter(UsbPolicy.company_id == endpoint.company_id).first()
        policy_value = policy.policy if policy else "allow_all"
        payload_device_id = str(data.payload.get("device_id", "")).strip()
        existing = None
        if payload_device_id:
            existing = db.query(UsbDevice).filter(
                UsbDevice.company_id == endpoint.company_id,
                UsbDevice.device_id == payload_device_id,
            ).first()
            if not existing:
                existing = UsbDevice(
                    company_id=endpoint.company_id,
                    device_id=payload_device_id,
                    device_name=str(data.payload.get("device_name", "")).strip(),
                    vendor=str(data.payload.get("vendor", "")).strip(),
                    size=str(data.payload.get("size", "")).strip(),
                    is_whitelisted=False,
                )
                db.add(existing)
                db.flush()
        is_whitelisted = bool(existing.is_whitelisted) if existing else False
        data.payload["is_whitelisted"] = is_whitelisted
        data.payload["policy"] = policy_value
        if policy_value == "block_all" or (policy_value == "whitelist" and not is_whitelisted):
            data.payload["action"] = "blocked"
            data.payload["usb_block_required"] = True
        else:
            data.payload["action"] = str(data.payload.get("action", "plugged")).lower()
            data.payload["usb_block_required"] = False

    risk = calculate_risk(
        data.event_type,
        data.payload,
        context={"endpoint_id": endpoint.id, "company_id": endpoint.company_id},
    )
    score = risk["risk_score"]; severity = risk["severity"]
    event = Event(
        company_id=endpoint.company_id, endpoint_id=endpoint.id,
        event_type=data.event_type, severity=severity,
        payload=data.payload, risk_score=str(score),
        flagged=risk["should_alert"]
    )
    db.add(event); db.flush()
    if score > int(endpoint.risk_score or 0):
        endpoint.risk_score = str(score)
    alert_id = None
    if risk["should_alert"]:
        explanation = generate_explanation(data.event_type, risk, endpoint.hostname)
        decision = risk.get("decision", "MONITOR")
        recommended = ", ".join(risk.get("recommended_actions", []))
        description = f"{risk['explanation']}\nDecision: {decision}\nActions: {recommended}"
        alert = Alert(
            company_id=endpoint.company_id, endpoint_id=endpoint.id, event_id=event.id,
            title=build_alert_title(data.event_type, risk["flags"], severity),
            description=description, severity=severity,
            risk_score=str(score), ai_explanation=explanation
        )
        db.add(alert); db.flush(); alert_id = alert.id

    decision = risk.get("decision")
    if decision in {DECISION_AUTO_BLOCK, DECISION_CRITICAL}:
        ip_to_block = data.payload.get("dest_ip") or data.payload.get("source_ip")
        if ip_to_block:
            auto_block_ip(
                db,
                endpoint.company_id,
                str(ip_to_block),
                f"Auto-block from decision engine ({decision})",
                blocked_by="ai_decision_engine",
            )

    if decision == DECISION_CRITICAL:
        endpoint.is_isolated = True
        endpoint.status = "isolated"
    elif decision == DECISION_ISOLATE and endpoint.status != "isolated":
        endpoint.status = "online"

    if alert_id:
        try:
            from app.realtime.ws import manager as ws_manager

            ws_manager.publish_alert(
                endpoint.company_id,
                {
                    "type": "alert_created",
                    "alert_id": alert_id,
                    "endpoint_id": endpoint.id,
                    "event_type": data.event_type,
                    "severity": severity,
                    "risk_score": score,
                    "decision": decision,
                    "created_at": datetime.utcnow().isoformat(),
                },
            )
        except Exception:
            pass

    db.commit()
    return {"event_id": event.id, "risk_score": score,
            "severity": severity, "alert_created": alert_id is not None, "alert_id": alert_id,
            "decision": decision, "recommended_actions": risk.get("recommended_actions", []),
            "response_actions": {
                "usb_action": "eject" if bool(data.payload.get("usb_block_required")) else None,
            }}


@router.get("/policies")
def get_agent_policies(db: Session = Depends(get_db), endpoint: Endpoint = Depends(get_current_agent)):
    seeded = False
    if db.query(AppBlacklist).filter(AppBlacklist.company_id == endpoint.company_id).count() == 0:
        for app_name, action in _DEFAULT_APP_BLACKLIST:
            db.add(AppBlacklist(company_id=endpoint.company_id, app_name=app_name, action=action, is_active=True))
        seeded = True
    if seeded:
        db.commit()
    usb_policy = db.query(UsbPolicy).filter(UsbPolicy.company_id == endpoint.company_id).first()
    usb_devices = db.query(UsbDevice).filter(
        UsbDevice.company_id == endpoint.company_id,
        UsbDevice.is_whitelisted == True,
    ).all()
    app_blacklist = db.query(AppBlacklist).filter(
        AppBlacklist.company_id == endpoint.company_id,
        AppBlacklist.is_active == True,
    ).all()
    domains = db.query(BlockedDomain).filter(
        BlockedDomain.company_id == endpoint.company_id,
        BlockedDomain.is_active == True,
    ).all()
    return {
        "usb_policy": usb_policy.policy if usb_policy else "allow_all",
        "usb_whitelist": [row.device_id for row in usb_devices],
        "app_blacklist": [{"app_name": row.app_name, "action": row.action} for row in app_blacklist],
        "blocked_domains": [{"domain": row.domain, "category": row.category} for row in domains],
    }


@router.get("/commands")
def get_agent_commands(limit: int = 20, db: Session = Depends(get_db), endpoint: Endpoint = Depends(get_current_agent)):
    rows = (
        db.query(AgentCommand)
        .filter(
            AgentCommand.company_id == endpoint.company_id,
            AgentCommand.endpoint_id == endpoint.id,
            AgentCommand.status == "pending",
        )
        .order_by(AgentCommand.created_at.asc())
        .limit(max(1, min(limit, 100)))
        .all()
    )
    return [
        {
            "id": row.id,
            "command_type": row.command_type,
            "payload": row.payload or {},
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/commands/{command_id}/result")
def set_command_result(
    command_id: str,
    data: CommandResultReq,
    db: Session = Depends(get_db),
    endpoint: Endpoint = Depends(get_current_agent),
):
    status = str(data.status or "").strip().lower()
    if status not in {"executed", "failed"}:
        raise HTTPException(status_code=400, detail="status must be executed or failed")
    row = db.query(AgentCommand).filter(
        AgentCommand.id == command_id,
        AgentCommand.company_id == endpoint.company_id,
        AgentCommand.endpoint_id == endpoint.id,
    ).first()
    if not row:
        raise HTTPException(status_code=404, detail="Command not found")
    row.status = status
    row.result_text = (data.result_text or "").strip()[:2000]
    row.executed_at = datetime.utcnow()
    db.commit()
    return {"message": "Command result updated"}


@router.post("/software-inventory")
def submit_software_inventory(
    data: SoftwareInventoryReq,
    db: Session = Depends(get_db),
    endpoint: Endpoint = Depends(get_current_agent),
):
    db.query(SoftwareInventory).filter(
        SoftwareInventory.company_id == endpoint.company_id,
        SoftwareInventory.endpoint_id == endpoint.id,
    ).delete()

    critical_count = 0
    high_count = 0
    for item in data.items:
        name = str(item.software_name or "").strip()
        if not name:
            continue
        key = name.lower()
        cve = _VULN_CATALOG.get(key)
        severity = cve.get("severity") if cve else None
        is_vuln = cve is not None
        if severity == "critical":
            critical_count += 1
        elif severity == "high":
            high_count += 1
        db.add(
            SoftwareInventory(
                company_id=endpoint.company_id,
                endpoint_id=endpoint.id,
                software_name=name,
                version=str(item.version or "").strip(),
                is_vulnerable=is_vuln,
                cve_id=cve.get("cve_id") if cve else None,
                severity=severity,
                last_scanned_at=datetime.utcnow(),
            )
        )
    db.flush()

    if critical_count or high_count:
        payload = {"critical_count": critical_count, "high_count": high_count}
        risk = calculate_risk("vulnerability", payload, context={"endpoint_id": endpoint.id, "company_id": endpoint.company_id})
        event = Event(
            company_id=endpoint.company_id,
            endpoint_id=endpoint.id,
            event_type="vulnerability",
            severity=risk["severity"],
            payload=payload,
            risk_score=str(risk["risk_score"]),
            flagged=risk["should_alert"],
        )
        db.add(event)
        db.flush()
        if risk["should_alert"]:
            alert = Alert(
                company_id=endpoint.company_id,
                endpoint_id=endpoint.id,
                event_id=event.id,
                title=build_alert_title("vulnerability", risk.get("flags", []), risk["severity"]),
                description=risk["explanation"],
                severity=risk["severity"],
                risk_score=str(risk["risk_score"]),
                ai_explanation=generate_explanation("vulnerability", risk, endpoint.hostname),
            )
            db.add(alert)
            db.flush()
            try:
                from app.realtime.ws import manager as ws_manager

                ws_manager.publish_alert(
                    endpoint.company_id,
                    {
                        "type": "alert_created",
                        "alert_id": alert.id,
                        "endpoint_id": endpoint.id,
                        "event_type": "vulnerability",
                        "severity": alert.severity,
                        "risk_score": int(alert.risk_score or 0),
                        "decision": risk.get("decision"),
                        "created_at": datetime.utcnow().isoformat(),
                    },
                )
            except Exception:
                pass
    db.commit()
    return {"message": "Software inventory updated", "critical_count": critical_count, "high_count": high_count}
