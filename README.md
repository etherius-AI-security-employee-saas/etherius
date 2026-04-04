# Etherius

High-trust AI cybersecurity platform for employee endpoint protection, multi-tenant security operations, and license-controlled SaaS delivery.

[![Public Site](https://img.shields.io/badge/Public%20Site-Live-0a8fff?style=for-the-badge)](https://etherius-security-site.vercel.app)
[![Dashboard](https://img.shields.io/badge/Dashboard-Live-18c9a6?style=for-the-badge)](https://etherius-security-dashboard.vercel.app)
[![API](https://img.shields.io/badge/API-Live-f7a948?style=for-the-badge)](https://etherius-security-api.vercel.app/health)

## Live Production Links

1. Public Website: `https://etherius-security-site.vercel.app`
2. Customer Dashboard: `https://etherius-security-dashboard.vercel.app`
3. Backend API: `https://etherius-security-api.vercel.app`
4. API Health Check: `https://etherius-security-api.vercel.app/health`

## Platform Scope

Etherius is not a single UI project. It is a complete security platform:

1. **Provider/CEO Control Plane**
   Subscription key issuance, seat licensing, and tenant provisioning.
2. **Customer SOC Dashboard**
   Threat visibility, endpoint monitoring, and operational workflows.
3. **Employee Shield Agent**
   Device enrollment, telemetry collection, heartbeat, and event submission.
4. **Public Distribution Front Door**
   Branded website for software delivery and product communication.

## What Makes Etherius Enterprise-Grade

1. Multi-tenant architecture with strict company isolation.
2. Seat-based subscription enforcement (commercial quantity controls).
3. Employee key lifecycle (issue/revoke/activation limits).
4. AI-assisted risk scoring and alert explanation.
5. Role-aware surface separation (provider vs customer vs employee).
6. Branded Windows binaries with taskbar identity.
7. Public web + dashboard + API deployed as distinct internet domains.

## Domain Wiring (Where Domains Are Needed)

### 1) Public marketing/download domain
Used by prospects and customers to discover and download.

### 2) Dashboard domain
Used by customer admins/security operators for daily operations.

### 3) Backend API domain
Used by:
1. Dashboard frontend (API calls).
2. Employee Shield clients (enrollment, heartbeat, events).

Without backend domain, dashboard and agents cannot operate globally.

## Repository Structure

1. `backend/`  
   FastAPI service, RBAC, tenant controls, licensing APIs, telemetry APIs.

2. `dashboard/`  
   React + Vite frontend for alerts, endpoints, response, and settings.

3. `agent/`  
   Employee Shield desktop client and collectors.

4. `suite/`  
   Branded desktop control center for startup/ops.

5. `website/`  
   Public high-visual landing and download site (Vercel deployed).

6. `installer/`  
   Build and packaging pipeline for Windows distribution.

## Security and Production Baseline

1. `ENV=production`
2. `ENABLE_API_DOCS=false`
3. `ENABLE_DEMO_SEED=false`
4. `SEED_COMPANY_DATA_ON_REGISTER=false`
5. Strong `SECRET_KEY`, `AGENT_SECRET_KEY`, `CEO_MASTER_KEY`
6. Explicit `CORS_ORIGINS` set to trusted dashboard/site domains

## Deployment Status

1. Public website deployed on Vercel.
2. Dashboard deployed on Vercel.
3. Backend API deployed on Vercel.
4. Cross-domain CORS configured for dashboard + site.

## Product Vision

Etherius is engineered to present premium UX while preserving hard security boundaries: a platform that looks elite, sells like SaaS, and operates like real security infrastructure.
