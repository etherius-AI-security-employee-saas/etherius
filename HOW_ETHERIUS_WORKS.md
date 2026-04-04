# How Etherius Works

Etherius is now positioned as one software product with two connected experiences:

- `Etherius Shield`
  The employee desktop protection app installed on company devices.
- `Etherius Control Center`
  The manager/admin dashboard used by security teams and company admins.

Together they form the full Etherius suite.

## What The Customer Buys

When a company buys Etherius, they are buying:

- the employee protection software
- the manager/admin dashboard
- the backend service that connects both sides

The dashboard is not a separate product. It is the control center for the employee software fleet.

## Who Uses What

### Employees

Employees install the Etherius desktop client on their computer.

That app:

- shows local protection status
- accepts a company enrollment code or activation code
- automatically captures hostname, OS, IP, and MAC
- sends endpoint telemetry to Etherius
- can raise suspicious event activity for manager review

### Managers And Admins

Managers and admins use the dashboard to:

- see all enrolled employee devices
- monitor alerts and suspicious events
- investigate incidents
- isolate or review endpoints
- manage users and access

## How The Full Flow Works

1. The admin starts Etherius Suite with `START_ETHERIUS.bat`.
2. The admin opens the dashboard and signs in.
3. The admin copies the company enrollment code from `Settings & Access`, or creates an endpoint activation code in `Endpoint Fleet`.
4. The employee installs and opens Etherius Shield.
5. The employee pastes the code into the app.
6. Etherius auto-registers the device with hostname, OS, IP, and MAC address.
7. The dashboard now shows that device inside `Endpoint Fleet`.
8. Future events, alerts, and status updates appear in the dashboard automatically.

## What Etherius Looks Like Now

### Top-level suite launcher

- [START_ETHERIUS.bat](C:/Users/Ganes/OneDrive/Desktop/etherius/START_ETHERIUS.bat)

This is the main entry point for the product.

### Employee protection software

- [START_AGENT.bat](C:/Users/Ganes/OneDrive/Desktop/etherius/START_AGENT.bat)
- [agent/ui/app.py](C:/Users/Ganes/OneDrive/Desktop/etherius/agent/ui/app.py)

### Manager dashboard

- [START_DASHBOARD.bat](C:/Users/Ganes/OneDrive/Desktop/etherius/START_DASHBOARD.bat)
- [dashboard](C:/Users/Ganes/OneDrive/Desktop/etherius/dashboard)

### Backend connection layer

- [START_BACKEND.bat](C:/Users/Ganes/OneDrive/Desktop/etherius/START_BACKEND.bat)
- [backend](C:/Users/Ganes/OneDrive/Desktop/etherius/backend)

## Current Product Status

Etherius is now a connected software suite.

That means:

- the employee desktop client exists
- the manager dashboard exists
- enrollment and activation flows exist
- device information automatically syncs to the dashboard

It is not yet a fully packaged commercial installer like Avast.

That future production phase would add:

- `.exe` packaging
- signed installer
- background service mode
- system tray mode
- production deployment and uptime tooling

## The Most Important Thing To Remember

If you only open the dashboard, you are seeing only the manager side.

If you want to see the employee software, open:

- [START_AGENT.bat](C:/Users/Ganes/OneDrive/Desktop/etherius/START_AGENT.bat)

If you want to see Etherius as one software suite, open:

- [START_ETHERIUS.bat](C:/Users/Ganes/OneDrive/Desktop/etherius/START_ETHERIUS.bat)
