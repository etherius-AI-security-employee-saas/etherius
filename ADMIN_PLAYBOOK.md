# Etherius Admin Playbook

## Purpose

This guide explains how an admin or manager uses Etherius in daily operations.

Etherius has three main parts:

- `backend`
  The API, authentication, alerting, and response logic.
- `dashboard`
  The web control center for admins and managers.
- `agent`
  The employee desktop software that sends telemetry into Etherius.

These are not separate products. Together they are the Etherius software suite.

## Start The Product

Recommended:

- Run `START_ETHERIUS.bat`

That opens the Etherius Suite launcher, which is the main product entry point.

Or separately:

- `START_BACKEND.bat`
- `START_DASHBOARD.bat`

## Open The Product

- Dashboard: `http://localhost:5173`
- API docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/health`

## Default Local Demo Admin

For local development:

- Email: `admin@etheriusdemo.com`
- Password: `Admin123!`

Change these before any real deployment.

## Daily Admin Workflow

1. Sign in to the dashboard.
2. Review `Security Overview` for endpoint health and open alerts.
3. Open `Alerts` to investigate suspicious activity.
4. Open `Endpoint Fleet` to inspect employee machines.
5. If needed, isolate an endpoint or block an IP.
6. Use `Audit Trail` to confirm all actions are recorded.
7. Use `Settings & Access` to add managers or other users.

## How To Add An Employee Device

1. Open `Endpoint Fleet`.
2. Click `Register Endpoint`.
3. Enter hostname, OS, IP, and MAC address.
4. Submit the registration.
5. Copy the generated:
   - `activation_code`
   - or `endpoint_id` and `agent_token`
6. On the employee machine, open the Etherius employee app.
7. Paste the activation code into the app.
8. Or copy the company enrollment code from `Settings & Access` and let the employee self-enroll.
9. Or manually update:
   - `agent/agent_config.json`
10. Start the employee software with:
   - `START_AGENT.bat`

## What The Employee App Looks Like Now

The employee software is now a visible local app instead of only a background process.

It shows:

- protection status
- connection and activation settings
- event and heartbeat counts
- recent protection activity
- auto-detected device info
- suspicious email review support

Main entry point:

- `python -m agent.ui.app`

## What The Employee Software Does

The employee software is the Python agent in:

- `agent`

It collects:

- process activity
- network activity
- login activity
- file activity

It sends that telemetry to the backend, where Etherius creates risk scores, events, and alerts that appear in the dashboard.

## User Roles

- `viewer`
  Read-only monitoring access.
- `manager`
  Operational security actions like device and incident handling.
- `admin`
  Full company administration and user management.

## Security Rules

- Never share agent tokens publicly.
- Never expose production secrets in source code.
- Rotate credentials if you suspect leakage.
- Use HTTPS and a production-grade database for real deployments.

## Reliability Notes

Local development is improved, but no local machine can honestly promise "never down."

For a production-grade Etherius deployment, add:

- managed PostgreSQL or equivalent
- process supervision or services
- backups
- monitoring and alerting
- HTTPS
- secret management
- deployment automation

## Troubleshooting

If the dashboard does not open:

1. Check `http://localhost:5173`
2. Restart `START_DASHBOARD.bat`

If the API does not respond:

1. Check `http://localhost:8000/health`
2. Restart `START_BACKEND.bat`

If an employee endpoint does not appear:

1. Recheck `agent/agent_config.json`
2. Confirm `backend_url`, `agent_token`, and `endpoint_id`
3. Restart `START_AGENT.bat`
