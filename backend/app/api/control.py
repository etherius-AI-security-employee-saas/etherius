from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.ai.insider_threat_ai import calculate_insider_threat_score
from app.database import get_db
from app.models.agent_command import AgentCommand
from app.models.app_blacklist import AppBlacklist
from app.models.blocked_domain import BlockedDomain
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.insider_threat_score import InsiderThreatScore
from app.models.software_inventory import SoftwareInventory
from app.models.usb_device import UsbDevice
from app.models.usb_policy import UsbPolicy
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.rbac import require_min_role

router = APIRouter(prefix="/api/dashboard", tags=["Control"])


class UsbPolicyReq(BaseModel):
    policy: str  # allow_all | block_all | whitelist


class UsbWhitelistReq(BaseModel):
    device_id: str
    device_name: Optional[str] = ""
    vendor: Optional[str] = ""
    size: Optional[str] = ""
    is_whitelisted: bool = True


class AppBlacklistReq(BaseModel):
    app_name: str
    action: str = "kill"  # alert | kill


class BlockedDomainReq(BaseModel):
    domain: str
    category: str = "custom"
    is_active: bool = True


_DEFAULT_BLACKLIST = [
    ("mimikatz", "kill"),
    ("netcat", "kill"),
    ("nc.exe", "kill"),
    ("qbittorrent", "alert"),
    ("utorrent", "alert"),
    ("tor", "alert"),
    ("brave-private-tor", "alert"),
]

_TOP_VULNERABLE_SOFTWARE = [
    "google chrome",
    "microsoft edge",
    "adobe reader",
    "java",
    "winrar",
    "7-zip",
    "openssh",
    "vmware tools",
]


def _sanitize_policy(policy: str) -> str:
    policy = str(policy or "").strip().lower()
    if policy not in {"allow_all", "block_all", "whitelist"}:
        raise HTTPException(status_code=400, detail="Policy must be allow_all, block_all, or whitelist")
    return policy


def _sanitize_action(action: str) -> str:
    action = str(action or "").strip().lower()
    if action not in {"alert", "kill"}:
        raise HTTPException(status_code=400, detail="Action must be alert or kill")
    return action


def _normalize_domain(domain: str) -> str:
    domain = str(domain or "").strip().lower()
    domain = domain.replace("https://", "").replace("http://", "").split("/")[0]
    if not domain:
        raise HTTPException(status_code=400, detail="Domain is required")
    return domain


@router.get("/usb-policy")
def get_usb_policy(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    item = db.query(UsbPolicy).filter(UsbPolicy.company_id == u.company_id).first()
    if not item:
        item = UsbPolicy(company_id=u.company_id, policy="allow_all")
        db.add(item)
        db.commit()
        db.refresh(item)
    return {"company_id": item.company_id, "policy": item.policy, "updated_at": item.updated_at}


@router.post("/usb-policy")
def set_usb_policy(data: UsbPolicyReq, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    policy = _sanitize_policy(data.policy)
    item = db.query(UsbPolicy).filter(UsbPolicy.company_id == u.company_id).first()
    if not item:
        item = UsbPolicy(company_id=u.company_id, policy=policy)
        db.add(item)
    else:
        item.policy = policy
    db.commit()
    return {"message": "USB policy updated", "policy": policy}


@router.get("/usb-whitelist")
def get_usb_whitelist(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    rows = db.query(UsbDevice).filter(UsbDevice.company_id == u.company_id).order_by(desc(UsbDevice.created_at)).all()
    return [
        {
            "id": row.id,
            "device_id": row.device_id,
            "device_name": row.device_name,
            "vendor": row.vendor,
            "size": row.size,
            "is_whitelisted": row.is_whitelisted,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/usb-whitelist")
def upsert_usb_whitelist(data: UsbWhitelistReq, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    row = db.query(UsbDevice).filter(
        UsbDevice.company_id == u.company_id,
        UsbDevice.device_id == data.device_id.strip(),
    ).first()
    if not row:
        row = UsbDevice(
            company_id=u.company_id,
            device_id=data.device_id.strip(),
            device_name=(data.device_name or "").strip(),
            vendor=(data.vendor or "").strip(),
            size=(data.size or "").strip(),
            is_whitelisted=bool(data.is_whitelisted),
        )
        db.add(row)
    else:
        row.device_name = (data.device_name or row.device_name or "").strip()
        row.vendor = (data.vendor or row.vendor or "").strip()
        row.size = (data.size or row.size or "").strip()
        row.is_whitelisted = bool(data.is_whitelisted)
    db.commit()
    return {"message": "USB whitelist updated", "device_id": row.device_id, "is_whitelisted": row.is_whitelisted}


def _ensure_default_blacklist(db: Session, company_id: str):
    existing = db.query(AppBlacklist).filter(AppBlacklist.company_id == company_id).count()
    if existing > 0:
        return
    for app_name, action in _DEFAULT_BLACKLIST:
        db.add(AppBlacklist(company_id=company_id, app_name=app_name, action=action, is_active=True))
    db.commit()


@router.get("/app-blacklist")
def get_app_blacklist(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    _ensure_default_blacklist(db, u.company_id)
    rows = db.query(AppBlacklist).filter(AppBlacklist.company_id == u.company_id, AppBlacklist.is_active == True).order_by(desc(AppBlacklist.created_at)).all()
    return [{"id": row.id, "app_name": row.app_name, "action": row.action, "created_at": row.created_at} for row in rows]


@router.post("/app-blacklist")
def add_app_blacklist(data: AppBlacklistReq, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    app_name = str(data.app_name or "").strip().lower()
    if not app_name:
        raise HTTPException(status_code=400, detail="app_name is required")
    action = _sanitize_action(data.action)
    row = db.query(AppBlacklist).filter(AppBlacklist.company_id == u.company_id, AppBlacklist.app_name == app_name).first()
    if not row:
        row = AppBlacklist(company_id=u.company_id, app_name=app_name, action=action, is_active=True)
        db.add(row)
    else:
        row.action = action
        row.is_active = True
    db.commit()
    return {"message": "App blacklist updated", "id": row.id}


@router.delete("/app-blacklist/{entry_id}")
def remove_app_blacklist(entry_id: str, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    row = db.query(AppBlacklist).filter(AppBlacklist.id == entry_id, AppBlacklist.company_id == u.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    row.is_active = False
    db.commit()
    return {"message": "Entry removed"}


@router.get("/blocked-domains")
def get_blocked_domains(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    rows = db.query(BlockedDomain).filter(BlockedDomain.company_id == u.company_id).order_by(desc(BlockedDomain.created_at)).all()
    return [
        {
            "id": row.id,
            "domain": row.domain,
            "category": row.category,
            "is_active": row.is_active,
            "created_at": row.created_at,
        }
        for row in rows
    ]


@router.post("/blocked-domains")
def add_blocked_domain(data: BlockedDomainReq, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    domain = _normalize_domain(data.domain)
    row = db.query(BlockedDomain).filter(BlockedDomain.company_id == u.company_id, BlockedDomain.domain == domain).first()
    if not row:
        row = BlockedDomain(
            company_id=u.company_id,
            domain=domain,
            category=str(data.category or "custom").strip().lower(),
            is_active=bool(data.is_active),
        )
        db.add(row)
    else:
        row.category = str(data.category or row.category or "custom").strip().lower()
        row.is_active = bool(data.is_active)
    db.commit()
    return {"message": "Blocked domain updated", "id": row.id}


@router.delete("/blocked-domains/{entry_id}")
def remove_blocked_domain(entry_id: str, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    row = db.query(BlockedDomain).filter(BlockedDomain.id == entry_id, BlockedDomain.company_id == u.company_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Entry not found")
    row.is_active = False
    db.commit()
    return {"message": "Domain disabled"}


@router.get("/insider-scores")
def insider_scores(
    endpoint_id: Optional[str] = Query(default=None),
    recalculate: bool = Query(default=False),
    db: Session = Depends(get_db),
    u: User = Depends(get_current_user),
):
    require_min_role("manager")(u)

    endpoint_query = db.query(Endpoint).filter(Endpoint.company_id == u.company_id)
    if endpoint_id:
        endpoint_query = endpoint_query.filter(Endpoint.id == endpoint_id)
    endpoints = endpoint_query.all()
    if not endpoints:
        return []

    if recalculate:
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        for endpoint in endpoints:
            rows = db.query(Event).filter(
                Event.company_id == u.company_id,
                Event.endpoint_id == endpoint.id,
                Event.created_at >= seven_days_ago,
            ).all()
            payload_rows = [
                {
                    "event_type": row.event_type,
                    "payload": row.payload,
                    "risk_score": row.risk_score,
                    "created_at": row.created_at,
                }
                for row in rows
            ]
            previous = db.query(InsiderThreatScore).filter(
                InsiderThreatScore.company_id == u.company_id,
                InsiderThreatScore.endpoint_id == endpoint.id,
            ).order_by(desc(InsiderThreatScore.calculated_at)).first()
            previous_score = int(previous.score) if previous else 0
            result = calculate_insider_threat_score(payload_rows, previous_score=previous_score)
            db.add(
                InsiderThreatScore(
                    company_id=u.company_id,
                    endpoint_id=endpoint.id,
                    score=int(result["score"]),
                    trend=result["trend"],
                    factors=result["factors"],
                    calculated_at=datetime.utcnow(),
                )
            )
        db.commit()

    out = []
    for endpoint in endpoints:
        latest = db.query(InsiderThreatScore).filter(
            InsiderThreatScore.company_id == u.company_id,
            InsiderThreatScore.endpoint_id == endpoint.id,
        ).order_by(desc(InsiderThreatScore.calculated_at)).first()
        if not latest:
            continue
        history = db.query(InsiderThreatScore).filter(
            InsiderThreatScore.company_id == u.company_id,
            InsiderThreatScore.endpoint_id == endpoint.id,
        ).order_by(desc(InsiderThreatScore.calculated_at)).limit(24).all()
        timeline = [{"score": row.score, "calculated_at": row.calculated_at} for row in reversed(history)]
        out.append(
            {
                "endpoint_id": endpoint.id,
                "hostname": endpoint.hostname,
                "score": latest.score,
                "trend": latest.trend,
                "factors": latest.factors or [],
                "calculated_at": latest.calculated_at,
                "timeline": timeline,
            }
        )
    out.sort(key=lambda x: int(x["score"]), reverse=True)
    return out


@router.get("/vulnerabilities")
def vulnerabilities(db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    rows = db.query(SoftwareInventory).filter(SoftwareInventory.company_id == u.company_id).order_by(desc(SoftwareInventory.last_scanned_at)).all()
    by_endpoint = {}
    for row in rows:
        bucket = by_endpoint.setdefault(
            row.endpoint_id,
            {"endpoint_id": row.endpoint_id, "vuln_count": 0, "critical_count": 0, "items": []},
        )
        if row.is_vulnerable:
            bucket["vuln_count"] += 1
            if str(row.severity or "").lower() == "critical":
                bucket["critical_count"] += 1
        bucket["items"].append(
            {
                "id": row.id,
                "software_name": row.software_name,
                "version": row.version,
                "is_vulnerable": row.is_vulnerable,
                "cve_id": row.cve_id,
                "severity": row.severity,
                "last_scanned_at": row.last_scanned_at,
            }
        )
    return {"endpoints": list(by_endpoint.values()), "known_watchlist": _TOP_VULNERABLE_SOFTWARE}


@router.get("/command-history")
def command_history(limit: int = Query(100, ge=1, le=500), db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("manager")(u)
    rows = db.query(AgentCommand).filter(AgentCommand.company_id == u.company_id).order_by(desc(AgentCommand.created_at)).limit(limit).all()
    return [
        {
            "id": row.id,
            "endpoint_id": row.endpoint_id,
            "command_type": row.command_type,
            "payload": row.payload,
            "status": row.status,
            "result_text": row.result_text,
            "created_at": row.created_at,
            "executed_at": row.executed_at,
        }
        for row in rows
    ]
