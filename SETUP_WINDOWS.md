# 🛡️ ETHERIUS — COMPLETE WINDOWS SETUP GUIDE
# Owner: YOU | Full Admin Access

---

## WHAT YOU OWN
- Backend API (FastAPI + PostgreSQL)
- AI Security Engine (behavior + anomaly detection)
- React Dashboard (dark premium UI)
- Agent software (runs on employee PCs)

---

## STEP 1 — INSTALL POSTGRESQL (if not done)

1. Download: https://www.postgresql.org/download/windows/
2. Install with default settings
3. When asked for a password — set it to: etherius123
   (or any password, then update .env file)
4. Port: 5432 (default, keep it)

After install, open pgAdmin or psql and run:
```sql
CREATE DATABASE etherius;
```

Or use pgAdmin → right click Databases → Create → Database → name it "etherius"

---

## STEP 2 — SETUP BACKEND

Open Command Prompt in the `etherius/backend` folder:

```cmd
cd C:\path\to\etherius\backend

python -m venv venv
venv\Scripts\activate

pip install -r requirements.txt

python init_db.py
```

You should see:
  ✓ companies
  ✓ users
  ✓ endpoints
  ✓ events
  ✓ alerts
  ✓ blocked_ips
  ✓ audit_logs

Then start the backend:
```cmd
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open browser: http://localhost:8000/docs
You should see the Etherius API docs.

---

## STEP 3 — SETUP DASHBOARD

Open a NEW Command Prompt in `etherius/dashboard`:

```cmd
cd C:\path\to\etherius\dashboard
npm install
npm run dev
```

Open browser: http://localhost:5173
You should see the Etherius login page.

---

## STEP 4 — CREATE YOUR FIRST ACCOUNT

Option A — use the dashboard Register tab
Option B — use the API:

Open http://localhost:8000/docs → POST /api/auth/register → Try it:
```json
{
  "company_name": "Your Company Name",
  "domain": "yourcompany.com",
  "admin_email": "admin@yourcompany.com",
  "admin_password": "YourPassword123!",
  "admin_full_name": "Your Name"
}
```

Then login at http://localhost:5173

---

## STEP 5 — REGISTER AN ENDPOINT (deploy agent)

1. Login to dashboard
2. Go to Endpoints → Register New Endpoint
3. Fill hostname, OS, IP
4. Copy the agent_token and endpoint_id from the response

5. On the target PC (or this PC for testing):
```cmd
cd C:\path\to\etherius\agent
pip install -r requirements.txt
```

6. Edit agent_config.json:
```json
{
  "backend_url": "http://YOUR_BACKEND_IP:8000",
  "agent_token": "PASTE_TOKEN_HERE",
  "endpoint_id": "PASTE_ID_HERE",
  "heartbeat_interval": 30
}
```

7. Run agent:
```cmd
python core/agent.py
```

---

## YOUR CREDENTIALS & SECRETS

Database:
  Host: localhost
  Port: 5432
  DB Name: etherius
  Password: etherius123 (as set in .env)

JWT Secret Keys (in backend/.env):
  SECRET_KEY=etherius_super_secret_key_change_in_production_2024
  AGENT_SECRET_KEY=etherius_agent_secret_key_change_in_production_2024

⚠ BEFORE GOING LIVE: Change both secret keys to random strings
  Run in Python: import secrets; print(secrets.token_hex(32))

---

## USER ROLES

| Role       | Can Do                                    |
|------------|-------------------------------------------|
| viewer     | View alerts and endpoints only            |
| manager    | + Register endpoints, block IPs           |
| admin      | + Create users, isolate endpoints         |
| superadmin | Full access across all companies          |

---

## API ENDPOINTS QUICK REFERENCE

| Endpoint                         | What it does              |
|----------------------------------|---------------------------|
| POST /api/auth/register          | Register company + admin  |
| POST /api/auth/login             | Login, get JWT token      |
| GET  /api/auth/me                | Get current user info     |
| POST /api/auth/users             | Create team member        |
| POST /api/agent/register         | Register new endpoint     |
| POST /api/agent/heartbeat        | Agent keepalive           |
| POST /api/agent/event            | Submit security event     |
| GET  /api/dashboard/stats        | Overview stats            |
| GET  /api/dashboard/alerts       | List alerts               |
| GET  /api/dashboard/endpoints    | List endpoints            |
| POST /api/response/block-ip      | Block an IP               |
| POST /api/response/isolate       | Isolate endpoint          |

---

## COMMON ERRORS & FIXES

ERROR: "No module named pydantic_settings"
FIX: pip install pydantic-settings

ERROR: "No module named jose"
FIX: pip install python-jose[cryptography]

ERROR: "could not connect to server" (PostgreSQL)
FIX: Make sure PostgreSQL is running
    Windows: Start → Services → postgresql → Start

ERROR: "database etherius does not exist"
FIX: Open pgAdmin → Create database named "etherius"

ERROR: "CORS" in browser console
FIX: Make sure backend is running on port 8000

ERROR: npm install fails
FIX: Delete node_modules folder and package-lock.json, then: npm install

---

## DEPLOYING ONLINE (to sell to companies)

1. Get a VPS (DigitalOcean, AWS, Hetzner)
2. Install PostgreSQL on VPS
3. Upload backend folder to VPS
4. Run: uvicorn app.main:app --host 0.0.0.0 --port 8000
5. Use nginx to proxy port 80/443 → 8000
6. Build dashboard: npm run build → serve with nginx
7. Change secret keys in .env to strong random strings
8. Change DATABASE_URL to production DB
9. Point your domain DNS to VPS IP

---

## ADD YOUR LOGO

In dashboard/index.html — replace the title
In dashboard/src/components/Sidebar.jsx — replace the Shield icon with your logo:
  <img src="/logo.png" width="32" height="32" style={{borderRadius:8}} />
Place logo.png in dashboard/public/logo.png

---

*Etherius v1.0.0 — Built for enterprise. Owned by you.*
