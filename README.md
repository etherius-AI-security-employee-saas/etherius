# Etherius

Enterprise endpoint security platform with one unified desktop software, license-controlled customer onboarding, and AI-assisted protection telemetry.

[![Website](https://img.shields.io/badge/Website-Live-f59f45?style=for-the-badge)](https://etherius-security-site.vercel.app)
[![API](https://img.shields.io/badge/API-Live-3fd0a3?style=for-the-badge)](https://etherius-security-api.vercel.app/health)

## Production Surface

1. Public website (download + manuals): `https://etherius-security-site.vercel.app`
2. Backend API (activation, licensing, telemetry): `https://etherius-security-api.vercel.app`

Manager dashboard is inside the desktop software and is not exposed as a public webpage by default.

## Core Value

1. One setup installer for both manager and employee.
2. CEO-controlled subscription issuance with strict employee seat quantity.
3. Manager dashboard unlocks only after subscription activation and manager sign-in.
4. Employees use the same app in employee mode without admin controls.
5. AI threat scoring, scan intelligence, and manager alert visibility.
6. Login/logout activity tracking and endpoint fleet status in manager view.

## Role Architecture

1. CEO
   Issues subscription keys, controls seat limits, tracks all customer fleets.
2. Customer Manager
   Activates company, generates employee keys, monitors endpoints and alerts.
3. Employee
   Activates endpoint protection and runs local AI scans in employee mode.

## Security Controls

1. Tenant isolation by company.
2. Subscription enforcement at login/enrollment/event APIs.
3. Employee key activation caps tied to purchased seats.
4. CEO-only license issuance endpoints using `X-CEO-Key`.
5. Advisory-first endpoint policy to avoid unnecessary business disruption.
6. Optional strict mode raises sensitivity and escalation recommendations.

## Cloud Requirements

1. Website domain (distribution + manuals).
2. API domain (all software communication).
3. Persistent production database (PostgreSQL recommended for cloud reliability).

## Repository Areas

1. `suite/` unified desktop software (manager + employee views)
2. `backend/` FastAPI service (auth, licensing, dashboard APIs, telemetry)
3. `agent/` endpoint collectors and runtime client
4. `ceo/` provider-only subscription control console
5. `website/` premium public download website
6. `installer/` setup packaging pipeline
7. `docs/` operations and deployment manuals

## Build Unified Setup

1. `powershell -ExecutionPolicy Bypass -File installer\build_release.ps1`
2. Output installer: `release\installer\Etherius-Setup.exe`
3. Output binary: `release\bin\EtheriusSuite.exe`

## Final Product Rule

Etherius customer delivery is one software setup only. No customer source-code access is required.
