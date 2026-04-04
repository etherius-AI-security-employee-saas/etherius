from datetime import datetime, timedelta
from typing import List

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.database import get_db
from app.models.endpoint import Endpoint
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
            "employee_limit": 0,
            "employees_used": db.query(func.count(Endpoint.id)).filter(Endpoint.company_id == current_user.company_id).scalar(),
            "employee_seats_remaining": 0,
        }

    is_valid = key.is_active and (not key.expires_at or key.expires_at >= datetime.utcnow())
    employees_used = db.query(func.count(Endpoint.id)).filter(Endpoint.company_id == current_user.company_id).scalar()
    employee_limit = int(key.seat_limit or 0)
    seats_remaining = max(employee_limit - employees_used, 0) if employee_limit > 0 else 0
    return {
        "status": "active" if is_valid else "expired",
        "is_active": is_valid,
        "expires_at": key.expires_at,
        "key_value": key.key_value,
        "employee_limit": employee_limit,
        "max_activations": key.max_activations,
        "current_activations": key.current_activations,
        "employees_used": employees_used,
        "employee_seats_remaining": seats_remaining,
    }


@router.post("/employee", response_model=LicenseOut, status_code=201)
def create_employee_key(
    payload: EmployeeLicenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    require_min_role("manager")(current_user)
    subscription = (
        db.query(LicenseKey)
        .filter(
            LicenseKey.company_id == current_user.company_id,
            LicenseKey.key_type == "subscription",
        )
        .first()
    )
    if not subscription or not subscription.is_active or (subscription.expires_at and subscription.expires_at < datetime.utcnow()):
        raise HTTPException(403, "Active customer subscription is required before generating employee keys")

    employee_limit = int(subscription.seat_limit or 0)
    employees_used = db.query(func.count(Endpoint.id)).filter(Endpoint.company_id == current_user.company_id).scalar()
    seats_remaining = max(employee_limit - employees_used, 0) if employee_limit > 0 else 0
    requested_activations = max(int(payload.max_activations or 1), 1)
    if employee_limit > 0:
        if seats_remaining <= 0:
            raise HTTPException(403, f"No employee seats remaining in this subscription ({employee_limit} total)")
        if requested_activations > seats_remaining:
            raise HTTPException(400, f"Requested max activations ({requested_activations}) exceeds remaining seats ({seats_remaining})")

    license_key = create_employee_license(
        db=db,
        company_id=current_user.company_id,
        issued_by_user_id=current_user.id,
        label=payload.label,
        max_activations=requested_activations,
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
    require_min_role("manager")(current_user)
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
    require_min_role("manager")(current_user)
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
        seat_limit=max(1, payload.employee_limit),
        max_activations=max(1, payload.max_activations),
        current_activations=0,
        is_active=True,
        expires_at=datetime.utcnow() + timedelta(days=max(1, payload.valid_days)),
    )
    db.add(subscription)
    db.commit()
    db.refresh(subscription)
    return subscription
