from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from app.database import get_db
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.company import Company
from app.models.alert import Alert
from app.schemas.endpoint import EndpointEnroll, EndpointRegister
from app.schemas.event import EventSubmit
from app.security.dependencies import get_current_agent, get_current_user
from app.security.enrollment import parse_company_code
from app.security.jwt_handler import create_agent_token
from app.security.licenses import validate_employee_key
from app.security.rbac import require_min_role
from app.ai.risk_engine import calculate_risk, build_alert_title
from app.ai.explain_ai import generate_explanation
from app.utils.audit import log_action

router = APIRouter(prefix="/api/agent", tags=["Agent"])

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
    activation_code = f"http://localhost:8000|{ep.id}|{token}"
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
    if existing:
        token = existing.agent_token or create_agent_token(existing.id, company_id)
        existing.agent_token = token
        existing.status = "online"
        if employee_license and employee_license.used_by_endpoint_id != existing.id:
            employee_license.current_activations += 1
            employee_license.last_used_at = datetime.utcnow()
            employee_license.used_by_endpoint_id = existing.id
        db.commit()
        activation_code = f"http://localhost:8000|{existing.id}|{token}"
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
    activation_code = f"http://localhost:8000|{ep.id}|{token}"
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
    risk = calculate_risk(data.event_type, data.payload)
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
        alert = Alert(
            company_id=endpoint.company_id, endpoint_id=endpoint.id, event_id=event.id,
            title=build_alert_title(data.event_type, risk["flags"], severity),
            description=risk["explanation"], severity=severity,
            risk_score=str(score), ai_explanation=explanation
        )
        db.add(alert); db.flush(); alert_id = alert.id
    db.commit()
    return {"event_id": event.id, "risk_score": score,
            "severity": severity, "alert_created": alert_id is not None, "alert_id": alert_id}
