# Etherius

Etherius is an enterprise-grade cyber defense platform built for organizations that need strict control, premium UX, and serious operational depth in one product.

## Why Etherius Is Different

1. One installer, dual-role intelligence:
   - same software for manager and employee
   - role boundaries enforced in-app by license and permissions
2. CEO-driven commercial control:
   - issue subscription keys with exact employee seat count
   - control activation, validity, and scaling from provider side
3. Real security telemetry loop:
   - endpoint activity flows to manager dashboard
   - login/logout behavior, risk scoring, alerts, and scan intelligence
4. Enterprise-safe protection model:
   - AI-assisted detection and escalation
   - advisory-first behavior to reduce business disruption

## Product Architecture

1. `suite/`
   Unified desktop product (manager activation, manager dashboard, employee protection mode).
2. `backend/`
   Private API for licensing, authentication, telemetry, and security workflows.
3. `ceo/`
   Provider-only control console for subscription issuance and customer fleet oversight.
4. `website/`
   Premium public distribution site that ships setup-only delivery.
5. `installer/`
   Setup build pipeline for production deployment.

## Security Boundary Model

1. CEO ownership boundary:
   - CEO master key controls private API surfaces and platform-level operations.
2. Customer manager boundary:
   - manager can control only their own employee fleet.
3. Employee boundary:
   - employee cannot access manager controls.
4. Tenant boundary:
   - strict company separation across telemetry and dashboard data.

## Setup-Only Customer Delivery

1. Build setup:
   `powershell -ExecutionPolicy Bypass -File installer\build_release.ps1`
2. Final installer:
   `release\installer\Etherius-Setup.exe`
3. Setup-only handoff folder:
   `SETUP_FOLDER` (ignored from git)

Customers should receive only installer output, never source code.

## CEO Documentation

1. `CEO_CONTROL_README.md`
2. `ceo/README.md`

Etherius is engineered to feel premium on the surface while operating like a disciplined security platform underneath.

## Release Trust (Important)

To avoid Windows SmartScreen "Unknown Publisher" warnings, production releases must be code signed.

Supported build-time signing options:

1. Certificate in PFX file:
   - `ETHERIUS_SIGN_PFX_PATH`
   - `ETHERIUS_SIGN_PFX_PASSWORD`
2. Certificate in Windows cert store:
   - `ETHERIUS_SIGN_CERT_SHA1`
3. Optional timestamp override:
   - `ETHERIUS_SIGN_TIMESTAMP_URL`

Build script will sign both:

1. `release/bin/EtheriusSuite.exe`
2. `release/installer/Etherius-Setup.exe`
