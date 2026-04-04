# Etherius Quick Start

## What This Project Is

Etherius is one software suite with three connected parts:

1. `backend`
   The service layer that connects everything.

2. `dashboard`
   The manager/admin control center at `http://localhost:5173`.

3. `agent`
   The employee protection app that runs on each machine and sends telemetry to the dashboard.

## Start The Project

Recommended launcher:

- Double-click `START_ETHERIUS.bat`

This now opens the Etherius Suite launcher, which acts as the top-level product entry point.

Manual launchers:

- `START_BACKEND.bat`
- `START_DASHBOARD.bat`
- `START_AGENT.bat`

## URLs

- Dashboard: `http://localhost:5173`
- Swagger API docs: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Default Demo Admin

For local development:

- Email: `admin@etheriusdemo.com`
- Password: `Admin123!`

Change these for production.

## How Managers Use Etherius

1. Sign in to the dashboard.
2. Review `Security Overview` and `Alerts`.
3. Open `Endpoint Fleet` to inspect employee devices.
4. Open `Settings & Access` and copy the company enrollment code, or register a specific endpoint from the dashboard.
5. Give that code to the employee.
6. The employee opens `START_AGENT.bat` on their machine.
7. The employee pastes the company code or activation code into the Etherius client.
8. The device auto-registers and sends hostname, OS, IP, and MAC to the dashboard.
9. Watch telemetry, alerts, audit logs, and blocked IPs update in the dashboard.

## How Employee Software Connects

The employee-side software is the Etherius Shield desktop client in:

- `agent`

Important file:

- `agent/agent_config.json`

It can be configured either by:

- enrollment/company code inside the app
- activation code inside the app
- or manual config values in `agent_config.json`

Manual config must contain:

- `backend_url`
- `agent_token`
- `endpoint_id`

Then run:

- `START_AGENT.bat`

## Important Security Notes

- Do not share `agent_token` values publicly.
- Do not commit real production secrets to Git.
- The demo admin is for local testing only.
- Rotate credentials if you think they were exposed.

## About Reliability

This setup is now much easier to run locally, but no local dev stack can honestly guarantee "never down."

For real production uptime, you would still want:

- a production database
- a process manager/service wrapper
- backups
- monitoring
- HTTPS and secret management
- deployment automation

## If Something Looks Wrong

1. Check the backend:
   Open `http://localhost:8000/health`

2. Check the dashboard:
   Open `http://localhost:5173`

3. If backend is not running:
   Start `START_BACKEND.bat`

4. If dashboard is not running:
   Start `START_DASHBOARD.bat`

5. If employee telemetry is missing:
   Recheck the company code, activation code, or `agent/agent_config.json` and restart `START_AGENT.bat`
