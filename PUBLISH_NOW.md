# Etherius Publish Manual (GitHub Org + Production Domain)

This gets your tool published safely while giving customers only software access.

## 1) Do you need WWW/domain?

No, but recommended.

- Without domain: use raw IP + port (not ideal).
- With domain: use `api.yourcompany.com` (recommended for customers).

## 2) What customers should get

Only executable package:

- `CUSTOMER_SETUP_ETHERIUS/`

Customers should never receive source code or CEO keys.

## 3) GitHub Organization publish

Run these commands from project root after you create an empty repo in your org:

```powershell
cd C:\Users\Ganes\OneDrive\Desktop\etherius
git add .
git commit -m "Production-ready customer/admin/employee packaging and security hardening"
git remote add origin https://github.com/<YOUR_ORG>/<YOUR_REPO>.git
git push -u origin master
```

If remote already exists:

```powershell
git remote set-url origin https://github.com/<YOUR_ORG>/<YOUR_REPO>.git
git push -u origin master
```

## 4) Production backend settings (`backend/.env`)

Set these before going live:

```env
ENV=production
ENABLE_API_DOCS=false
ENABLE_DEMO_SEED=false
SEED_COMPANY_DATA_ON_REGISTER=false
SECRET_KEY=<LONG_RANDOM_SECRET>
AGENT_SECRET_KEY=<LONG_RANDOM_SECRET>
CEO_MASTER_KEY=<LONG_RANDOM_SECRET>
DATABASE_URL=<POSTGRES_URL_OR_SECURE_DB>
CORS_ORIGINS=https://<YOUR_DASHBOARD_DOMAIN>
```

## 5) Launch production backend

From server:

```powershell
cd backend
venv\Scripts\python.exe run_backend.py
```

Keep it always on using a service manager (NSSM/PM2/system service).

## 6) Dashboard publishing options

### Option A (recommended): serve dashboard from backend

1. Build dashboard:

```powershell
cd dashboard
npm install
npm run build
```

2. Backend serves it at:
- `https://<YOUR_API_DOMAIN>/dashboard`

### Option B: Vercel dashboard + separate backend

If using Vercel, set dashboard env:

- `VITE_API_BASE_URL=https://<YOUR_API_DOMAIN>`
- `VITE_ROUTER_BASENAME=/`

Then deploy dashboard to Vercel.

## 7) CEO workflow after publish

1. Keep CEO key private.
2. Issue customer subscriptions via:
- `POST /api/licenses/subscription/issue`
3. Set `employee_limit` per contract (example 300).
4. Send only customer package + subscription key.

## 8) Customer onboarding after publish

1. Customer admin runs `admin\ADMIN_START_ETHERIUS.bat`
2. Registers with subscription key.
3. Generates employee keys.
4. Employees run `employee\EMPLOYEE_START_SHIELD.bat`.

## 9) Security checklist before first customer

1. Docs disabled in production.
2. Strong secrets configured.
3. HTTPS enabled on domain.
4. Database backup enabled.
5. Only customer package shared (no source/private keys).
