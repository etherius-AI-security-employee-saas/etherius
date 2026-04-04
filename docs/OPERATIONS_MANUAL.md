# Etherius Operations Manual

## 1) Product Boundaries (Public vs Protected)

### Public

1. Public website download page.
2. Customer package download.

### Protected

1. Customer dashboard data and controls (requires account + token).
2. Customer registration (requires valid subscription key).
3. CEO subscription issuance and customer fleet overview (requires CEO master key).

## 2) CEO Workflow (Provider Side)

Use `ceo/CEO_START_CONSOLE.bat` (provider-only):

1. Enter API URL and CEO master key.
2. Issue a customer subscription key:
   - seat limit (example: 100, 300)
   - valid days
   - company activations
3. Send this subscription key privately to the customer admin.
4. Use CEO customer overview table to monitor:
   - seat usage
   - online endpoints
   - open alerts
   - login/logout totals

## 3) Customer Admin Workflow

1. Open customer dashboard URL.
2. First-time setup:
   - Register company
   - Enter subscription key from CEO
3. Daily operations:
   - Open `Employee Access` page
   - Generate employee keys (based on purchased seat quantity)
   - Share company code + employee key to each employee
   - Track endpoint status, risk, alerts, and login/logout activity

If the customer does not have a valid subscription key, registration is blocked.

## 4) Employee Workflow

1. Install Etherius Shield.
2. Enter:
   - company enrollment code
   - employee key
   - backend URL (default is cloud API)
3. Enroll device.
4. Protection starts and telemetry is sent to customer dashboard.

## 5) What Is Enforced

1. Seat limits per customer subscription.
2. Employee key activation limits.
3. Tenant isolation by company ID.
4. Dashboard API auth required.
5. CEO-only endpoints protected by master key.
6. Inactive/expired customer subscription blocks dashboard and agent API access.

## 6) Current Live Production URLs

1. Public site: `https://etherius-security-site.vercel.app`
2. Customer dashboard: `https://etherius-security-dashboard.vercel.app`
3. API: `https://etherius-security-api.vercel.app`
