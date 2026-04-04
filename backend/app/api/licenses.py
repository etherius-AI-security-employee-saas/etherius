from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.license_key import LicenseKey
from app.models.user import User
from app.schemas.auth import EmployeeLicenseCreate, LicenseOut, SubscriptionLicenseCreate
from app.security.dependencies import get_current_user
from app.security.licenses import create_employee_license, generate_license_value
from app.security.rbac import require_min_role
from app.utils.audit import log_action

router = APIRouter(prefix="/api/licenses", tags=["Licenses"])


@router.get("/subscription")
def subscription_status(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    key = (
        db.query(LicenseKey)
        .filter(
            LicenseKey.company_id == current_user.company_id,
            LicenseKey.key_type == "subscription",
        )
        .first()
    )
    if not key:
        return {
            "status": "missing",
            "is_active": False,
            "expires_at": None,
            "key_value": None,
        }

    is_valid = key.is_active and (not key.expires_at or key.expires_at >= datetime.utcnow())
    return {
        "status": "active" if is_valid else "expired",
        "is_active": is_valid,
        "expires_at": key.expires_at,
        "key_value": key.key_value,
        "max_activations": key.max_activations,
        "current_activations": key.current_activations,
    }


@router.post("/employee", response_model=LicenseOut, status_code=201)
def create_employee_key(
    payload: EmployeeLicenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_min_role("admin")(current_user)
    license_key = create_employee_license(
        db=db,
        company_id=current_user.company_id,
        issued_by_user_id=current_user.id,
        label=payload.label,
        max_activations=payload.max_activations,
        valid_days=payload.valid_days,
    )
    log_action(
        db,
        current_user.id,
        current_user.company_id,
        "CREATE_EMPLOYEE_LICENSE",
        "license_key",
        license_key.id,
    )
    return license_key


@router.get("/employee", response_model=List[LicenseOut])
def list_employee_keys(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_min_role("admin")(current_user)
    return (
        db.query(LicenseKey)
        .filter(
            LicenseKey.company_id == current_user.company_id,
            LicenseKey.key_type == "employee",
        )
        .order_by(LicenseKey.created_at.desc())
        .all()
    )


@router.patch("/employee/{license_id}/revoke")
def revoke_employee_key(
    license_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_min_role("admin")(current_user)
    key = (
        db.query(LicenseKey)
        .filter(
            LicenseKey.id == license_id,
            LicenseKey.company_id == current_user.company_id,
            LicenseKey.key_type == "employee",
        )
        .first()
    )
    if not key:
        raise HTTPException(404, "Employee license key not found")
    key.is_active = False
    db.commit()
    log_action(
        db,
        current_user.id,
        current_user.company_id,
        "REVOKE_EMPLOYEE_LICENSE",
        "license_key",
        key.id,
    )
    return {"message": "Employee key revoked"}


@router.post("/subscription/issue", response_model=LicenseOut, status_code=201)
def issue_subscription_key(
    payload: SubscriptionLicenseCreate,
    x_ceo_key: str = Header(default=""),
    db: Session = Depends(get_db),
):
    if x_ceo_key != settings.CEO_MASTER_KEY:
        raise HTTPException(401, "Invalid CEO master key")

    subscription = LicenseKey(
        key_value=generate_license_value("ETH-SUB"),
        key_type="subscription",
        label=payload.label or "Customer Subscription",
        max_activations=max(1, payload.max_activations),
        current_activations=0,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=max(1, payload.valid_days)),
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription
