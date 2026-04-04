from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

database_url = settings.DATABASE_URL.strip()
engine_kwargs = {
    "pool_pre_ping": True,
    "echo": False,
}

if database_url.startswith("sqlite"):
    engine_kwargs["connect_args"] = {"check_same_thread": False}
else:
    engine_kwargs["pool_size"] = 10
    engine_kwargs["max_overflow"] = 20

engine = create_engine(database_url, **engine_kwargs)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    from app.models.company import Company
    from app.models.user import User
    from app.models.endpoint import Endpoint
    from app.models.event import Event
    from app.models.alert import Alert
    from app.models.blocked_ip import BlockedIP
    from app.models.audit_log import AuditLog
    from app.models.license_key import LicenseKey
    Base.metadata.create_all(bind=engine)
    _apply_lightweight_migrations()
    print("[Etherius] Database tables created successfully")


def _column_exists(conn, table_name: str, column_name: str) -> bool:
    rows = conn.execute(text(f"PRAGMA table_info({table_name})")).fetchall()
    return any(row[1] == column_name for row in rows)


def _add_column_if_missing(conn, table_name: str, column_name: str, ddl_type: str):
    if not _column_exists(conn, table_name, column_name):
        conn.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {ddl_type}"))


def _apply_lightweight_migrations():
    # Lightweight SQLite-safe migrations for existing local installs.
    if not database_url.startswith("sqlite"):
        return
    with engine.begin() as conn:
        _add_column_if_missing(conn, "companies", "subscription_key", "TEXT")
        _add_column_if_missing(conn, "companies", "subscription_status", "TEXT DEFAULT 'active'")
        _add_column_if_missing(conn, "companies", "subscription_expires_at", "DATETIME")
        _add_column_if_missing(conn, "companies", "license_enforcement", "BOOLEAN DEFAULT 1")

        _add_column_if_missing(conn, "license_keys", "used_by_endpoint_id", "TEXT")
        _add_column_if_missing(conn, "license_keys", "seat_limit", "INTEGER DEFAULT 10")

def check_db():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"[Etherius] DB connection failed: {e}")
        return False
