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
1. Open `EtheriusSuite.exe`
2. Go to `Admin Activation + Dashboard`
3. Register company with subscription key from CEO
4. Sign in and generate employee keys
5. Share:
- Company Enrollment Code
- One employee key per employee
6. Monitor endpoint status, alerts, logins, and logouts

## Employee Flow
1. Open the same `EtheriusSuite.exe`
2. Go to `Employee Activation + Protection`
3. Paste Company Enrollment Code + Employee Key
4. Click `Enroll Employee Device` and then `Start Protection`
5. Optional: run `Quick AI Threat Scan` or `Deep Corporate Risk Scan`

## Important Security Boundaries
1. No subscription key = no customer registration/login usage
2. Expired subscription = dashboard and agent API access blocked
3. Customer manager UI is limited to employee operations
4. CEO-only endpoints require `X-CEO-Key`
