# Etherius

Enterprise-grade AI cybersecurity platform for employee endpoint defense, real-time threat intelligence, and license-controlled SaaS distribution.

Public Download Website: https://website-ecru-seven-71.vercel.app

## Why Etherius Is Different

Etherius is designed as a full-stack security operations system, not just a dashboard:

1. Multi-tenant architecture with strict company isolation.
2. Subscription-based seat control (sell 100, 300, 1000+ employees safely).
3. Controlled employee enrollment with license enforcement.
4. Live endpoint telemetry with risk scoring and alerting.
5. AI-powered explanation pipeline for analyst-friendly threat context.
6. Response workflows for isolation and containment actions.
7. Customer-safe distribution model (EXE package, no source required).

## Core Product Surfaces

1. `backend/`  
   FastAPI + SQLAlchemy service for auth, licensing, telemetry ingestion, dashboard APIs, and tenancy enforcement.

2. `dashboard/`  
   React operations console for customer administrators and security analysts.

3. `agent/`  
   Employee Shield client for endpoint enrollment, heartbeat, event capture, suspicious email analysis, and protection workflow.

4. `suite/`  
   Branded Control Center desktop launcher for operational startup and health visibility.

5. `CUSTOMER_SETUP_ETHERIUS/`  
   Deployment-ready customer package with separate manuals for customer admins and employees.

## Security Highlights

1. Role-based access control with admin/manager/viewer boundaries.
2. Cross-tenant protection and company-scoped data access.
3. Subscription key issuance with CEO master key gate.
4. Seat-based employee quantity enforcement.
5. Employee key generation, revocation, and activation tracking.
6. Production hardening switches:
   - `ENV=production`
   - `ENABLE_API_DOCS=false`
   - `ENABLE_DEMO_SEED=false`
   - `SEED_COMPANY_DATA_ON_REGISTER=false`

## Customer SaaS Sales Model

Etherius is built for commercial rollout:

1. CEO/provider issues subscription per customer with seat limit.
2. Customer admin registers company and generates employee keys.
3. Employee installs Shield and enrolls with company code + employee key.
4. New enrollments are blocked automatically when seat limit is reached.

## Stunning Operational Depth

Etherius combines the visual polish of modern SaaS with the control rigor of enterprise security tooling:

1. One-click operations startup.
2. Real-time telemetry + endpoint state.
3. AI-assisted threat interpretation.
4. Defensive response controls.
5. Branded Windows binaries with taskbar/icon identity.
6. Clear role split between provider, customer admin, and employee users.

## Quick Start (Dev)

1. Backend:
```powershell
cd backend
venv\Scripts\python.exe run_backend.py
```

2. Dashboard (dev mode):
```powershell
cd dashboard
npm install
npm run dev
```

3. Full local suite:
```powershell
START_ETHERIUS.bat
```

## Production Publish

See:

- `PUBLISH_NOW.md`
- `CUSTOMER_SETUP_ETHERIUS/CUSTOMER_README.md`
- `CUSTOMER_SETUP_ETHERIUS/CUSTOMER_ADMIN_MANUAL.md`
- `CUSTOMER_SETUP_ETHERIUS/EMPLOYEE_MANUAL.md`

## Vision

Etherius is engineered to feel like a premium, high-trust security platform: controlled, scalable, and deployable at real business scale across organizations and employee fleets.

## Public Download Site

The standalone public download experience is located in:

- `website/`

Deploy this folder to Vercel as a dedicated marketing/download front door.
