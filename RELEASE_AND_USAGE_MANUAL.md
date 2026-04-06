# Etherius Release + Usage Manual

This is the required release rule for every new feature:

1. Develop feature in code.
2. Run validation (`python -m compileall`, dashboard build, smoke tests).
3. Build latest setup (`Etherius-Setup.exe`).
4. Replace public download binary in `website/downloads/`.
5. Deploy backend + website (manager dashboard is inside software).
6. Push commit to GitHub.
7. Publish short manual update for CEO, Customer Admin, Employee.

If one step is missing, the feature is **not considered released**.

## Current Production Endpoints

- Site: https://etherius-security-site.vercel.app
- API: https://etherius-security-api.vercel.app
- Manager dashboard: inside Etherius software only (no public web dashboard)

## Roles and Access

## CEO (You)

1. Create company subscription/license with employee limit.
2. Send only customer license details to Customer Admin.
3. Keep Swagger/API operational access private (CEO only).
4. Review global operations and support escalations.

## Customer Admin (Company Manager)

1. Install Etherius setup.
2. Activate using company admin license key.
3. Open Admin section inside software (role-gated).
4. Issue employee activation keys up to licensed quantity.
5. Monitor employee status, detections, alerts, login/logout.

## Employee

1. Install same Etherius setup.
2. Activate with employee key from Customer Admin.
3. Protection modules run in background.
4. Employee sees only allowed section (no admin controls).

## Release Checklist Template (Use Every Time)

1. Feature name + version bump:
2. Backend/API updated:
3. Agent updated:
4. Software UI updated:
5. Setup rebuilt:
6. Website download replaced:
7. Production deploy completed:
8. GitHub commit hash:
9. Manual usage notes:
