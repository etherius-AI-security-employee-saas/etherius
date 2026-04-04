# Etherius Operations Manual

## 1) Product Scope

Etherius is delivered as one desktop software (`EtheriusSuite.exe`) for both manager and employee roles.

1. Employee sees only employee protection flow by default.
2. Manager dashboard appears only after manager action and successful manager authentication.
3. CEO operations are separate in provider-only console.

## 2) Public vs Protected

### Public

1. Download website.
2. Installer package endpoint.
3. API health endpoint.

### Protected

1. Company registration (requires valid subscription key).
2. Manager dashboard APIs (requires manager JWT).
3. Employee enrollment/event APIs (requires active subscription and activation token).
4. CEO licensing APIs (requires `X-CEO-Key`).

## 3) CEO Runbook

1. Open `ceo/CEO_START_CONSOLE.bat`.
2. Enter API URL and CEO master key.
3. Issue subscription key:
   - employee seat limit (example: 300)
   - valid days
   - max company activations
4. Share subscription key privately with customer manager.
5. Use customer overview table for:
   - employees used/remaining
   - online endpoints
   - open alerts
   - login/logout counts

## 4) Customer Manager Runbook

1. Install and open Etherius software.
2. Click `Manager View`.
3. Activate company with:
   - company info
   - manager email/password
   - subscription key from CEO
4. Sign in to unlock manager dashboard.
5. Generate employee keys (capacity is limited by purchased seat count).
6. Share to employees:
   - company enrollment code
   - employee activation key
7. Monitor:
   - endpoint status
   - open alerts
   - scan telemetry
   - login/logout activity

## 5) Employee Runbook

1. Install the same Etherius software.
2. Stay in `Employee Protection` view.
3. Enter:
   - API URL (pre-filled default)
   - company enrollment code
   - employee activation key
4. Click:
   - `Enroll Employee Device`
   - `Apply Activation Code`
   - `Start Protection`
5. Optional:
   - `Quick AI Threat Scan`
   - `Deep Corporate Risk Scan`

## 6) AI Security Posture

1. Process and command-line behavior heuristics.
2. Suspicious network port pattern checks.
3. Sensitive filesystem/script checks.
4. Email lure indicator scoring.
5. Local quick/deep scan intelligence sent to manager dashboard.
6. Advisory-first defaults to avoid unnecessary blocking of business workflows.

## 7) Cloud Requirements

1. Website domain for distribution.
2. API domain for activation + telemetry.
3. Persistent production database (`DATABASE_URL` set to PostgreSQL recommended).

## 8) Production Environment Baseline

1. `ENV=production`
2. `ENABLE_API_DOCS=false`
3. `ENABLE_WEB_DASHBOARD=false`
4. `ENABLE_DEMO_SEED=false`
5. `SEED_COMPANY_DATA_ON_REGISTER=false`
6. Strong values for:
   - `SECRET_KEY`
   - `AGENT_SECRET_KEY`
   - `CEO_MASTER_KEY`
