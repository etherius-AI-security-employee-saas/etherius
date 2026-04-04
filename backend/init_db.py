"""Run this to create all tables: python init_db.py"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import Base, check_db, engine
from app.models.alert import Alert
from app.models.audit_log import AuditLog
from app.models.blocked_ip import BlockedIP
from app.models.company import Company
from app.models.endpoint import Endpoint
from app.models.event import Event
from app.models.license_key import LicenseKey
from app.models.user import User

print("Checking database connection...")
if not check_db():
    print("ERROR: Cannot connect to database.")
    print("Check DATABASE_URL in .env and make sure the selected database is available")
    sys.exit(1)

print("Creating tables...")
Base.metadata.create_all(bind=engine)
print("Tables created:")
for t in Base.metadata.tables:
    print(f"  - {t}")
print("\nDatabase ready! You can now run: uvicorn app.main:app --reload")
