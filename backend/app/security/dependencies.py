from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from app.database import get_db
from app.security.jwt_handler import decode_token
from app.models.user import User
from app.models.endpoint import Endpoint
from app.security.subscription_guard import enforce_active_company_subscription

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    payload = decode_token(credentials.credentials, "access")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    user = db.query(User).filter(
        User.id == payload["user_id"],
        User.is_active == True
    ).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found or disabled")
    enforce_active_company_subscription(db, user.company_id, detail="Customer subscription is inactive or expired")
    return user

def get_current_agent(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> Endpoint:
    payload = decode_token(credentials.credentials, "agent")
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid agent token")
    endpoint = db.query(Endpoint).filter(
        Endpoint.id == payload["sub"],
        Endpoint.company_id == payload["company_id"]
    ).first()
    if not endpoint:
        raise HTTPException(status_code=401, detail="Endpoint not registered")
    enforce_active_company_subscription(db, endpoint.company_id, detail="Customer subscription is inactive or expired")
    return endpoint
