# Etherius First Customer Guide (Simple)

## 1) Start the product
1. Double-click `START_ETHERIUS.bat`.
2. Wait for browser to open `http://localhost:8000/dashboard`.
3. Keep backend CMD window open while using Etherius.

If CMD window closes, backend stops. This is normal in local/self-hosted mode.

## 2) Create admin company
1. Open dashboard login page.
2. Click Register Company.
3. Fill:
- Company name
- Admin email/password
- Subscription key

## 3) Create employee access keys
1. Login as admin.
2. Go to Settings.
3. Create Employee License Key.
4. Copy:
- Company Enrollment Code
- Employee License Key

## 4) Employee installation flow
1. Employee installs/runs `START_AGENT.bat`.
2. Employee pastes:
- Company Enrollment Code
- Employee License Key
3. Click Enroll This Device.
4. Click Start Protection.

## 5) How to test quickly
1. Open `http://localhost:8000/docs` and verify health API.
2. In dashboard, check Endpoints page.
3. Start one agent and confirm endpoint appears in dashboard.

## 6) Customer handover checklist
- Admin login works
- Subscription key accepted
- Employee license key generation works
- Employee endpoint enrollment works
- Dashboard shows endpoint/alerts/events
