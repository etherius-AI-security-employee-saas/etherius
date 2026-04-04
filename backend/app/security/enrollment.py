import hashlib

from app.config import settings


def build_company_code(company_id: str) -> str:
    signature = hashlib.sha256(f"{company_id}:{settings.SECRET_KEY}".encode()).hexdigest()[:10].upper()
    return f"ETH-{company_id}-{signature}"


def parse_company_code(code: str) -> str | None:
    if not code.startswith("ETH-"):
        return None
    if len(code) <= 15 or code[-11] != "-":
        return None
    company_id = code[4:-11]
    signature = code[-10:]
    if build_company_code(company_id) != code:
        return None
    return company_id
