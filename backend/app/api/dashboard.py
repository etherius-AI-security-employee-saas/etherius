from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from typing import Optional, List
from app.database import get_db
from app.models.alert import Alert
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.user import User
from app.models.blocked_ip import BlockedIP
from app.models.audit_log import AuditLog
from app.schemas.alert import AlertOut, AlertUpdate
from app.schemas.endpoint import EndpointOut
from app.security.dependencies import get_current_user
from app.security.rbac import require_min_role

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/stats")
def stats(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    cid = u.company_id
    total_ep = db.query(Endpoint).filter(Endpoint.company_id == cid).count()
    online_ep = db.query(Endpoint).filter(Endpoint.company_id == cid, Endpoint.status == "online").count()
    open_alerts = db.query(Alert).filter(Alert.company_id == cid, Alert.status == "open").count()
    critical = db.query(Alert).filter(Alert.company_id == cid, Alert.status == "open", Alert.severity == "critical").count()
    high = db.query(Alert).filter(Alert.company_id == cid, Alert.status == "open", Alert.severity == "high").count()
    today_events = db.query(Event).filter(
        Event.company_id == cid,
        func.date(Event.created_at) == func.current_date()
    ).count()
    blocked_ips = db.query(BlockedIP).filter(BlockedIP.company_id == cid, BlockedIP.is_active == True).count()
    return {
        "total_endpoints": total_ep, "online_endpoints": online_ep,
        "offline_endpoints": total_ep - online_ep,
        "open_alerts": open_alerts, "critical_alerts": critical,
        "high_alerts": high, "events_today": today_events,
        "blocked_ips": blocked_ips
    }

@router.get("/alerts", response_model=List[AlertOut])
def get_alerts(status: Optional[str] = None, severity: Optional[str] = None,
               limit: int = Query(50, le=200), offset: int = 0,
               db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    q = db.query(Alert).filter(Alert.company_id == u.company_id)
    if status: q = q.filter(Alert.status == status)
    if severity: q = q.filter(Alert.severity == severity)
    return q.order_by(desc(Alert.created_at)).offset(offset).limit(limit).all()

@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: str, data: AlertUpdate,
                 db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    alert = db.query(Alert).filter(Alert.id == alert_id, Alert.company_id == u.company_id).first()
    if not alert: raise HTTPException(404, "Alert not found")
    if data.status: alert.status = data.status
    if data.assigned_to: alert.assigned_to = data.assigned_to
    db.commit()
    return {"message": "Updated"}

@router.get("/endpoints", response_model=List[EndpointOut])
def get_endpoints(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    return db.query(Endpoint).filter(Endpoint.company_id == u.company_id).all()

@router.get("/endpoints/{endpoint_id}/events")
def endpoint_events(endpoint_id: str, limit: int = Query(50, le=200),
                    db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    ep = db.query(Endpoint).filter(Endpoint.id == endpoint_id, Endpoint.company_id == u.company_id).first()
    if not ep: raise HTTPException(404, "Endpoint not found")
    evs = db.query(Event).filter(Event.endpoint_id == endpoint_id).order_by(desc(Event.created_at)).limit(limit).all()
    return [{"id":e.id,"event_type":e.event_type,"severity":e.severity,
             "risk_score":e.risk_score,"created_at":e.created_at} for e in evs]

@router.get("/blocked-ips")
def blocked_ips(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("admin")(u)
    ips = db.query(BlockedIP).filter(BlockedIP.company_id == u.company_id, BlockedIP.is_active == True).all()
    return [{"id":i.id,"ip":i.ip_address,"reason":i.reason,"created_at":i.created_at} for i in ips]

@router.get("/audit-logs")
def audit_logs(limit: int = Query(50, le=200),
               db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("admin")(u)
    logs = db.query(AuditLog).filter(AuditLog.company_id == u.company_id).order_by(desc(AuditLog.created_at)).limit(limit).all()
    return [{"id":l.id,"actor_id":l.actor_id,"action":l.action,
             "resource":l.resource,"details":l.details,"created_at":l.created_at} for l in logs]
