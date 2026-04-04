# CEO Control Readme

Use this as provider-side control only (do not share with customers).

## Start CEO Console

Run:

`ceo/CEO_START_CONSOLE.bat`

## What CEO Can Do

1. Create customer subscription keys with exact employee quantity.
2. Set validity days and company activation limits.
3. Monitor customer seat usage and endpoint activity.
4. Review customer alert and login/logout totals.
5. Access private CEO API routes:
   - `/api/ceo/health`
   - `/api/ceo/swagger` (when `ENABLE_API_DOCS=true`)

## What CEO Shares to Customer

Only the subscription key.  
Never share CEO master key or source code.
