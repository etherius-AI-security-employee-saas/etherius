import secrets
import string
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.license_key import LicenseKey


ALPHABET = string.ascii_uppercase + string.digits


def _random_chunk(size: int = 5) -> str:
    return "".join(secrets.choice(ALPHABET) for _ in range(size))


def generate_license_value(prefix: str) -> str:
    return f"{prefix}-{_random_chunk()}-{_random_chunk()}-{_random_chunk()}"


def ensure_default_subscription_key(db: Session) -> str:
    default_key = getattr(settings, "DEMO_SUBSCRIPTION_KEY", "ETH-SUB-DEMO-2026-START")
    existing = db.query(LicenseKey).filter(LicenseKey.key_value == default_key).first()
    if existing:
        return default_key
    lic = LicenseKey(
        key_value=default_key,
        key_type="subscription",
        label="Default Demo Subscription",
        max_activations=1,
        current_activations=0,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=3650),
    )
    db.add(lic)
    db.commit()
    return default_key


def validate_employee_key(
    db: Session,
    employee_key: str,
    company_id: Optional[str] = None,
    endpoint_id: Optional[str] = None,
    now: Optional[datetime] = None,
) -> Optional[LicenseKey]:
    now = now or datetime.utcnow()
    key_query = db.query(LicenseKey).filter(
        LicenseKey.key_value == employee_key.strip(),
        LicenseKey.key_type == "employee",
    )
    if company_id:
        key_query = key_query.filter(LicenseKey.company_id == company_id)
    key = key_query.first()
    if not key:
        return None
    if not key.is_active:
        return None
    if key.expires_at and key.expires_at < now:
        return None
    if key.current_activations >= key.max_activations and key.used_by_endpoint_id != endpoint_id:
        return None
    return key


def validate_subscription_key(
    db: Session,
    subscription_key: str,
    now: Optional[datetime] = None,
) -> Optional[LicenseKey]:
    now = now or datetime.utcnow()
    key = db.query(LicenseKey).filter(
        LicenseKey.key_value == subscription_key.strip(),
        LicenseKey.key_type == "subscription",
    ).first()
    if not key:
        return None
    if not key.is_active:
        return None
    if key.expires_at and key.expires_at < now:
        return None
    if key.current_activations >= key.max_activations:
        return None
    return key


def create_employee_license(
    db: Session,
    company_id: str,
    issued_by_user_id: str,
    label: Optional[str] = None,
    max_activations: int = 1,
    valid_days: int = 365,
) -> LicenseKey:
    license_key = LicenseKey(
        company_id=company_id,
        issued_by_user_id=issued_by_user_id,
        key_value=generate_license_value("ETH-EMP"),
        key_type="employee",
        label=label,
        max_activations=max(max_activations, 1),
        current_activations=0,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=max(valid_days, 1)),
    )
    db.add(license_key)
    db.commit()
    db.refresh(license_key)
    return license_key
