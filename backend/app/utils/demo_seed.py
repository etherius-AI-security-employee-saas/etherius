from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.blocked_ip import BlockedIP
from app.models.company import Company
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.user import User
from app.security.password import hash_password


def seed_company_data(db: Session, company: Company, admin_user: User) -> None:
    has_endpoints = db.query(Endpoint).filter(Endpoint.company_id == company.id).count() > 0
    if has_endpoints:
        return

    now = datetime.utcnow()
    endpoints = [
        Endpoint(
            company_id=company.id,
            hostname="SOC-WORKSTATION-01",
            os="Windows 11 Pro",
            ip_address="10.0.1.24",
            mac_address="00:15:5D:2A:91:11",
            agent_version="1.0.0",
            status="online",
            risk_score="82",
            last_seen=now - timedelta(minutes=2),
        ),
        Endpoint(
            company_id=company.id,
            hostname="EDGE-GATEWAY-02",
            os="Ubuntu 24.04",
            ip_address="10.0.5.10",
            mac_address="00:15:5D:2A:91:12",
            agent_version="1.0.0",
            status="isolated",
            is_isolated=True,
            risk_score="91",
            last_seen=now - timedelta(minutes=6),
        ),
        Endpoint(
            company_id=company.id,
            hostname="FINANCE-LT-07",
            os="Windows 11 Enterprise",
            ip_address="10.0.3.88",
            mac_address="00:15:5D:2A:91:13",
            agent_version="1.0.0",
            status="offline",
            risk_score="28",
            last_seen=now - timedelta(hours=3),
        ),
    ]
    db.add_all(endpoints)
    db.flush()

    events = [
        Event(
            company_id=company.id,
            endpoint_id=endpoints[0].id,
            event_type="failed_login_burst",
            severity="high",
            payload={"username": "svc-admin", "attempts": 9, "source_ip": "185.77.21.19"},
            risk_score="82",
            flagged=True,
            created_at=now - timedelta(minutes=18),
        ),
        Event(
            company_id=company.id,
            endpoint_id=endpoints[1].id,
            event_type="suspicious_powershell",
            severity="critical",
            payload={"command": "EncodedCommand execution", "user": "SYSTEM"},
            risk_score="91",
            flagged=True,
            created_at=now - timedelta(minutes=9),
        ),
        Event(
            company_id=company.id,
            endpoint_id=endpoints[2].id,
            event_type="usb_mass_storage_detected",
            severity="medium",
            payload={"device": "Unknown USB storage", "user": "analyst.temp"},
            risk_score="28",
            flagged=False,
            created_at=now - timedelta(hours=2),
        ),
    ]
    db.add_all(events)
    db.flush()

    alerts = [
        Alert(
            company_id=company.id,
            endpoint_id=endpoints[0].id,
            event_id=events[0].id,
            title="Brute-force login pattern detected",
            description="Repeated failed sign-in attempts were detected against a privileged account.",
            severity="high",
            status="open",
            risk_score="82",
            ai_explanation="Pattern analysis shows credential stuffing behavior against a privileged identity from an unfamiliar source IP.",
            created_at=now - timedelta(minutes=17),
        ),
        Alert(
            company_id=company.id,
            endpoint_id=endpoints[1].id,
            event_id=events[1].id,
            title="Suspicious remote execution activity",
            description="An encoded PowerShell execution chain suggests active hands-on-keyboard behavior.",
            severity="critical",
            status="investigating",
            risk_score="91",
            ai_explanation="Command telemetry strongly resembles staged post-exploitation behavior and warrants immediate containment.",
            assigned_to=admin_user.id,
            created_at=now - timedelta(minutes=8),
        ),
    ]
    db.add_all(alerts)

    blocked = BlockedIP(
        company_id=company.id,
        ip_address="185.77.21.19",
        reason="Automatic containment after repeated failed login attempts",
        blocked_by=admin_user.id,
        is_active=True,
        created_at=now - timedelta(minutes=15),
    )
    db.add(blocked)

    audit_entries = [
        AuditLog(
            company_id=company.id,
            actor_id=admin_user.id,
            action="LOGIN",
            resource="user",
            resource_id=admin_user.id,
            details="Initial demo administrator sign-in",
            created_at=now - timedelta(minutes=30),
        ),
        AuditLog(
            company_id=company.id,
            actor_id=admin_user.id,
            action="REGISTER_ENDPOINT",
            resource="endpoint",
            resource_id=endpoints[0].id,
            details="SOC-WORKSTATION-01 enrolled into tenant",
            created_at=now - timedelta(minutes=28),
        ),
        AuditLog(
            company_id=company.id,
            actor_id=admin_user.id,
            action="BLOCK_IP",
            resource="blocked_ip",
            resource_id=blocked.id,
            details=blocked.ip_address,
            created_at=now - timedelta(minutes=15),
        ),
    ]
    db.add_all(audit_entries)
    db.commit()


def bootstrap_demo_environment(db: Session, company_name: str, admin_email: str, admin_password: str) -> User:
    admin_user = db.query(User).filter(User.email == admin_email).first()
    if admin_user:
        company = db.query(Company).filter(Company.id == admin_user.company_id).first()
        if company:
            seed_company_data(db, company, admin_user)
        return admin_user

    company = db.query(Company).filter(Company.name == company_name).first()
    if not company:
        company = Company(name=company_name, domain="etheriusdemo.com")
        db.add(company)
        db.flush()

    admin_user = User(
        company_id=company.id,
        email=admin_email,
        password_hash=hash_password(admin_password),
        full_name="Demo Administrator",
        role="admin",
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)

    seed_company_data(db, company, admin_user)
    return admin_user
