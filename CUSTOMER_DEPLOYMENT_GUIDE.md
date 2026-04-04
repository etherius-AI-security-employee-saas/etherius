# Etherius Customer Deployment Guide

## What A Buying Company Gets

When a company buys Etherius, they receive:

- the dashboard for managers and admins
- the backend security platform
- the employee endpoint security client
- the workflow to connect employee devices into a single security console

## Standard Customer Onboarding Model

### 1. Create The Customer Tenant

Register the customer company using the dashboard or API.

This creates:

- the company record
- the initial admin user
- the customer workspace

### 2. Give The Customer Admin Access

The customer admin uses the dashboard to:

- create managers
- review alerts
- register employee devices
- handle response actions

### 3. Roll Out The Employee Client

For each employee device:

1. Register the device in `Endpoint Fleet`
2. Generate the activation code and endpoint credentials
3. Deliver the employee security client
4. Paste the activation code into the client
5. Launch the employee app

### 4. Start Monitoring

Once agents are installed, the customer sees:

- endpoint status
- live events
- alert timelines
- blocked IPs
- audit history

## Recommended Commercial Packaging

Position Etherius as:

- a cybersecurity operations platform for growing companies
- a device monitoring and incident response layer
- a managed security console for admins and managers

## Suggested Product Tiers

### Starter

- small endpoint count
- core dashboard
- basic alerts and response

### Growth

- more endpoints
- more managers
- richer reporting
- stronger support

### Enterprise

- large multi-team deployments
- custom integrations
- SLA support
- advanced hosting and compliance options

## Production Checklist Before Selling

Before giving Etherius to external customers, complete these items:

1. Move from local SQLite to a production database.
2. Replace demo credentials and development defaults.
3. Use HTTPS.
4. Add proper secret management.
5. Run backend and dashboard as supervised services.
6. Add backup and restore procedures.
7. Add monitoring and uptime alerts.
8. Add logging retention and access controls.
9. Prepare legal terms, privacy policy, and support process.
10. Document installation for customer IT teams.

## Security Positioning

Do not promise "never down" or "zero risk."

Professional positioning is:

- proactive monitoring
- centralized visibility
- faster response
- better operational control
- reduced detection and response time

## Customer-Facing Explanation

Etherius connects employee devices to a central security dashboard. Managers can view endpoint health, investigate alerts, isolate suspicious machines, block malicious IP addresses, and maintain an audit trail of actions across the organization.
