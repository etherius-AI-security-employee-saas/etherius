from datetime import datetime
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.license_key import LicenseKey


def get_company_subscription(db: Session, company_id: str) -> Optional[LicenseKey]:
    return (
        db.query(LicenseKey)
        .filter(
            LicenseKey.company_id == company_id,
            LicenseKey.key_type == "subscription",
        )
        .order_by(LicenseKey.created_at.desc())
        .first()
    )


def has_active_company_subscription(db: Session, company_id: str, now: Optional[datetime] = None) -> bool:
    now = now or datetime.utcnow()
    company = db.query(Company).filter(Company.id == company_id, Company.is_active == True).first()
    if not company:
        return False
    if company.subscription_status == "suspended":
        return False

    subscription = get_company_subscription(db, company_id)
    if not subscription:
        return False
    if not subscription.is_active:
        return False
    if subscription.expires_at and subscription.expires_at < now:
        return False
    return True


def enforce_active_company_subscription(db: Session, company_id: str, detail: str = "Active subscription required"):
    if not has_active_company_subscription(db, company_id):
        raise HTTPException(status_code=403, detail=detail)
