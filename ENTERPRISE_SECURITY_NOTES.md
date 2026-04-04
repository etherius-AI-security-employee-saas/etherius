# Enterprise Security Notes

No software is 100% unattackable. Etherius can be made highly resistant with layered controls.

## Already Added
- Strong password policy (12+ chars, upper/lower/number/symbol)
- Login brute-force lock (temporary lock after repeated failures)
- Security HTTP headers (CSP, frame deny, no-sniff, permissions policy)
- License-gated onboarding (subscription + employee key model)

## Must-Do Before Production Customer Rollout
1. Run behind HTTPS reverse proxy (Nginx/Caddy/IIS).
2. Set real secret keys in `backend/.env`:
- `SECRET_KEY`
- `AGENT_SECRET_KEY`
- `CEO_MASTER_KEY`
3. Restrict firewall to allowed IP ranges.
4. Add MFA for admin accounts.
5. Add centralized logs and alerts.
6. Run dependency and penetration testing regularly.

## CEO Key Issuance
- Endpoint: `POST /api/licenses/subscription/issue`
- Header: `X-CEO-Key: <CEO_MASTER_KEY>`
- Body:
```json
{
  "label": "Customer A - Annual Plan",
  "max_activations": 1,
  "valid_days": 365
}
```
- Output contains a subscription key to give to that customer admin.
