# Etherius

Enterprise endpoint security suite with one desktop software for manager and employee roles.

[Website](https://etherius-security-site.vercel.app)  
[API Health](https://etherius-security-api.vercel.app/health)

## Clean Structure

1. `suite/` unified desktop app code
2. `backend/` licensing + telemetry API
3. `ceo/` provider-only console
4. `website/` public download site
5. `installer/` setup builder

## Setup-Only Delivery

1. Build setup:
   `powershell -ExecutionPolicy Bypass -File installer\build_release.ps1`
2. Final installer:
   `release\installer\Etherius-Setup.exe`
3. Local clean customer handoff folder:
   `SETUP_FOLDER` (ignored from git, setup file only)

Customers should receive only `Etherius-Setup.exe`, not source code.

## CEO Docs

Use `CEO_CONTROL_README.md` or `ceo/README.md`.
