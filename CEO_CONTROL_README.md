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
6. Approve signed production releases only (avoid distributing unsigned installer builds).

## Legal Trust Baseline for Customer Downloads

1. Purchase an OV or EV code-signing certificate from a trusted CA.
2. Export certificate as `.pfx` with password.
3. Run `ceo/CEO_BUILD_SIGNED_RELEASE.bat` (double-click).
4. Enter your `.pfx` full path and password when prompted.
5. Confirm signature status is `Valid` before sharing installer.

If signature is not `Valid`, do not distribute setup.

## What CEO Shares to Customer

Only the subscription key.  
Never share CEO master key or source code.
