from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from app.database import get_db
from app.models.endpoint import Endpoint
from app.models.user import User
from app.security.dependencies import get_current_user
from app.security.rbac import require_min_role
from app.security.ip_blocker import block_ip as do_block
from app.utils.audit import log_action

router = APIRouter(prefix="/api/response", tags=["Response"])

class BlockIPReq(BaseModel):
    ip_address: str
    reason: Optional[str] = "Manual block"

class IsolateReq(BaseModel):
    endpoint_id: str
    reason: Optional[str] = "Security incident"

@router.post("/block-ip")
def block_ip(data: BlockIPReq, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("admin")(u)
    r = do_block(db, u.company_id, data.ip_address, data.reason, u.id)
    log_action(db, u.id, u.company_id, "BLOCK_IP", "blocked_ip", r.id, data.ip_address)
    return {"message": f"IP {data.ip_address} blocked", "id": r.id}

@router.post("/isolate")
def isolate(data: IsolateReq, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("admin")(u)
    ep = db.query(Endpoint).filter(Endpoint.id == data.endpoint_id, Endpoint.company_id == u.company_id).first()
    if not ep: raise HTTPException(404, "Endpoint not found")
    ep.is_isolated = True; ep.status = "isolated"; db.commit()
    log_action(db, u.id, u.company_id, "ISOLATE", "endpoint", ep.id, data.reason)
    return {"message": f"{ep.hostname} isolated"}

@router.post("/unisolate")
def unisolate(data: IsolateReq, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("admin")(u)
    ep = db.query(Endpoint).filter(Endpoint.id == data.endpoint_id, Endpoint.company_id == u.company_id).first()
    if not ep: raise HTTPException(404, "Endpoint not found")
    ep.is_isolated = False; ep.status = "online"; db.commit()
    return {"message": f"{ep.hostname} restored"}

@router.delete("/unblock-ip/{ip_id}")
def unblock_ip(ip_id: str, db: Session = Depends(get_db), u: User = Depends(get_current_user)):
    require_min_role("admin")(u)
    from app.models.blocked_ip import BlockedIP
    ip = db.query(BlockedIP).filter(BlockedIP.id == ip_id, BlockedIP.company_id == u.company_id).first()
    if not ip: raise HTTPException(404, "Not found")
    ip.is_active = False; db.commit()
    return {"message": "IP unblocked"}
