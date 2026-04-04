from datetime import datetime, timedelta
from typing import Optional
from jose import jwt, JWTError
from app.config import settings

def create_access_token(user_id: str, email: str, company_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    return jwt.encode({
        "sub": email, "user_id": user_id,
        "company_id": company_id, "role": role,
        "type": "access", "exp": expire
    }, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_refresh_token(user_id: str, email: str, company_id: str, role: str) -> str:
    expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    return jwt.encode({
        "sub": email, "user_id": user_id,
        "company_id": company_id, "role": role,
        "type": "refresh", "exp": expire
    }, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

def create_agent_token(endpoint_id: str, company_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.AGENT_TOKEN_EXPIRE_HOURS)
    return jwt.encode({
        "sub": endpoint_id, "company_id": company_id,
        "type": "agent", "exp": expire
    }, settings.AGENT_SECRET_KEY, algorithm=settings.ALGORITHM)

def decode_token(token: str, token_type: str = "access") -> Optional[dict]:
    secret = settings.AGENT_SECRET_KEY if token_type == "agent" else settings.SECRET_KEY
    try:
        payload = jwt.decode(token, secret, algorithms=[settings.ALGORITHM])
        if payload.get("type") != token_type:
            return None
        return payload
    except JWTError:
        return None
