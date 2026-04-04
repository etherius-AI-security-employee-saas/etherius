from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog
from app.utils.logger import get_logger

logger = get_logger("audit")

def log_action(db: Session, actor_id: str, company_id: str,
               action: str, resource: str = None,
               resource_id: str = None, details: str = None,
               ip_address: str = None):
    try:
        entry = AuditLog(
            company_id=company_id, actor_id=actor_id,
            action=action, resource=resource,
            resource_id=resource_id, details=details,
            ip_address=ip_address
        )
        db.add(entry)
        db.commit()
    except Exception as e:
        logger.warning(f"Audit log failed: {e}")
