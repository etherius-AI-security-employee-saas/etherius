import re
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from datetime import datetime
from app.config import settings
from app.database import get_db
from app.models.company import Company
from app.models.user import User
from app.schemas.auth import CompanyRegister, UserLogin, UserCreate, TokenResponse
from app.security.password import hash_password, verify_password
from app.security.enrollment import build_company_code
from app.security.jwt_handler import create_access_token, create_refresh_token
from app.security.dependencies import get_current_user
from app.security.rbac import require_min_role
from app.security.licenses import validate_subscription_key
from app.security.subscription_guard import enforce_active_company_subscription
from app.utils.demo_seed import seed_company_data
from app.utils.audit import log_action

router = APIRouter(prefix="/api/auth", tags=["Auth"])
FAILED_LOGINS = {}
MAX_FAILED_ATTEMPTS = 5
LOCK_MINUTES = 15


def _password_is_strong(password: str) -> bool:
    if len(password or "") < 12:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    if not re.search(r"[^A-Za-z0-9]", password):
        return False
    return True


def _client_login_key(request: Request, email: str) -> str:
    host = request.client.host if request.client else "unknown"
    return f"{host}:{(email or '').strip().lower()}"


def _is_login_locked(key: str) -> bool:
    record = FAILED_LOGINS.get(key)
    if not record:
        return False
    locked_until = record.get("locked_until")
    if not locked_until:
        return False
    if datetime.utcnow() >= locked_until:
        FAILED_LOGINS.pop(key, None)
        return False
    return True


def _record_failed_login(key: str):
    now = datetime.utcnow()
    record = FAILED_LOGINS.get(key, {"count": 0, "locked_until": None, "updated_at": now})
    record["count"] += 1
    record["updated_at"] = now
    if record["count"] >= MAX_FAILED_ATTEMPTS:
        record["locked_until"] = now + timedelta(minutes=LOCK_MINUTES)
    FAILED_LOGINS[key] = record


def _clear_failed_login(key: str):
    FAILED_LOGINS.pop(key, None)

@router.post("/register", status_code=201)
def register(data: CompanyRegister, db: Session = Depends(get_db)):
    if db.query(Company).filter(Company.name == data.company_name).first():
        raise HTTPException(400, "Company name already exists")
    subscription = validate_subscription_key(db, data.subscription_key)
    if not subscription:
        raise HTTPException(400, "Invalid or expired subscription key")
    if not _password_is_strong(data.admin_password):
        raise HTTPException(400, "Password must be at least 12 chars and include upper, lower, number, and symbol")

    try:
        company = Company(
            name=data.company_name,
            domain=data.domain,
            subscription_key=subscription.key_value,
            subscription_status="active",
            subscription_expires_at=subscription.expires_at,
            max_endpoints=max(1, subscription.seat_limit or 10),
        )
        db.add(company)
        db.flush()
        user = User(
            company_id=company.id, email=data.admin_email,
            password_hash=hash_password(data.admin_password),
            full_name=data.admin_full_name, role="manager"
        )
        db.add(user)
        db.flush()
        subscription.company_id = company.id
        subscription.issued_by_user_id = user.id
        subscription.current_activations += 1
        subscription.last_used_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        db.refresh(company)
        if settings.SEED_COMPANY_DATA_ON_REGISTER:
            seed_company_data(db, company, user)
        return {"message": "Company registered", "company_id": company.id}
    except IntegrityError:
        db.rollback()
        raise HTTPException(400, "A user with that email already exists for this company")
    except Exception as exc:
        db.rollback()
        raise HTTPException(500, f"Registration failed: {exc}")

@router.post("/login", response_model=TokenResponse)
def login(data: UserLogin, request: Request, db: Session = Depends(get_db)):
    key = _client_login_key(request, data.email)
    if _is_login_locked(key):
        raise HTTPException(429, f"Too many failed logins. Try again in {LOCK_MINUTES} minutes")
    user = db.query(User).filter(User.email == data.email, User.is_active == True).first()
    if not user or not verify_password(data.password, user.password_hash):
        _record_failed_login(key)
        raise HTTPException(401, "Invalid credentials")
    enforce_active_company_subscription(db, user.company_id, detail="Customer subscription is inactive or expired")
    if user.role not in {"admin", "superadmin", "manager"}:
        raise HTTPException(403, "Dashboard access is restricted to admin accounts")
    _clear_failed_login(key)
    user.last_login = datetime.utcnow(); db.commit()
    log_action(db, user.id, user.company_id, "LOGIN", "user", user.id)
    return TokenResponse(
        access_token=create_access_token(user.id, user.email, user.company_id, user.role),
        refresh_token=create_refresh_token(user.id, user.email, user.company_id, user.role),
        user_id=user.id, company_id=user.company_id,
        role=user.role, full_name=user.full_name
    )

@router.get("/me")
def me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id, "email": current_user.email,
        "full_name": current_user.full_name, "role": current_user.role,
        "company_id": current_user.company_id,
        "company_code": build_company_code(current_user.company_id)
    }

@router.post("/users", status_code=201)
def create_user(data: UserCreate, db: Session = Depends(get_db),
                current_user: User = Depends(get_current_user)):
    require_min_role("admin")(current_user)
    if not _password_is_strong(data.password):
        raise HTTPException(400, "Password must be at least 12 chars and include upper, lower, number, and symbol")
    if db.query(User).filter(User.email == data.email,
                              User.company_id == current_user.company_id).first():
        raise HTTPException(400, "Email already exists")
    user = User(
        company_id=current_user.company_id, email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name, role=data.role
    )
    db.add(user); db.commit()
    log_action(db, current_user.id, current_user.company_id, "CREATE_USER", "user", user.id)
    return {"message": "User created", "user_id": user.id}

@router.get("/users")
def list_users(db: Session = Depends(get_db),
               current_user: User = Depends(get_current_user)):
    require_min_role("admin")(current_user)
    users = db.query(User).filter(User.company_id == current_user.company_id).all()
    return [{"id":u.id,"email":u.email,"full_name":u.full_name,
             "role":u.role,"is_active":u.is_active,"last_login":u.last_login} for u in users]
