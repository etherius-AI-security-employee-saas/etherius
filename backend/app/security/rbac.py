from fastapi import HTTPException
from app.models.user import User

ROLE_LEVEL = {"superadmin": 4, "admin": 3, "manager": 2, "viewer": 1}

def require_role(*roles):
    def check(current_user: User):
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail=f"Access denied. Required: {list(roles)}")
        return current_user
    return check

def require_min_role(min_role: str):
    min_level = ROLE_LEVEL.get(min_role, 0)
    def check(current_user: User):
        if ROLE_LEVEL.get(current_user.role, 0) < min_level:
            raise HTTPException(status_code=403, detail=f"Minimum role required: {min_role}")
        return current_user
    return check

def check_tenant(user: User, company_id: str):
    if user.role != "superadmin" and user.company_id != company_id:
        raise HTTPException(status_code=403, detail="Cross-tenant access denied")
