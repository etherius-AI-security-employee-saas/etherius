# Etherius START HERE

## Quick Rule
Customer operations run on cloud domains. Customer admins do not need source code access.

## Live URLs
1. Public download site: `https://etherius-security-site.vercel.app`
2. Customer dashboard: `https://etherius-security-dashboard.vercel.app`
3. API: `https://etherius-security-api.vercel.app`

## CEO Provider Flow
1. Open provider-only console: `ceo/CEO_START_CONSOLE.bat`
2. Issue subscription key with seat count (example: 300 employees)
3. Send that subscription key privately to customer admin
4. Customer cannot register without this key

## Customer Admin Flow
1. Open dashboard URL and click Register Company
2. Enter subscription key from CEO
3. Open `Employee Access` page and generate employee keys
4. Share:
- Company Enrollment Code
- One employee key per employee
5. Monitor endpoint status, alerts, logins, and logouts

## Employee Flow
1. Install `EtheriusShield.exe` from customer package
2. Paste Company Enrollment Code + Employee Key
3. Click `Enroll This Device`
4. Shield starts protection and appears in dashboard

## Important Security Boundaries
1. No subscription key = no customer registration/login usage
2. Expired subscription = dashboard and agent API access blocked
3. Customer manager UI is limited to employee operations
4. CEO-only endpoints require `X-CEO-Key`
