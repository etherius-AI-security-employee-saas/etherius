from sqlalchemy.orm import Session
from app.models.blocked_ip import BlockedIP
from datetime import datetime

def is_blocked(db: Session, company_id: str, ip: str) -> bool:
    r = db.query(BlockedIP).filter(
        BlockedIP.company_id == company_id,
        BlockedIP.ip_address == ip,
        BlockedIP.is_active == True
    ).first()
    if not r:
        return False
    if r.expires_at and r.expires_at < datetime.utcnow():
        r.is_active = False
        db.commit()
        return False
    return True

def block_ip(db: Session, company_id: str, ip: str, reason: str, blocked_by: str = "auto"):
    existing = db.query(BlockedIP).filter(
        BlockedIP.company_id == company_id,
        BlockedIP.ip_address == ip
    ).first()
    if existing:
        existing.is_active = True
        existing.reason = reason
        db.commit()
        return existing
    r = BlockedIP(company_id=company_id, ip_address=ip, reason=reason, blocked_by=blocked_by)
    db.add(r)
    db.commit()
    return r
