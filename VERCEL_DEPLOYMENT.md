# Vercel Deployment Notes

## Recommended Production Split

For a professional deployment, do **not** treat this as one single app hosted in one place.

Recommended:

1. Deploy `dashboard/` to Vercel
2. Deploy `backend/` to a backend-friendly host
   - Render
   - Railway
   - Fly.io
   - VPS / cloud VM
3. Use a managed PostgreSQL database
4. Point the dashboard to the backend with:
   - `VITE_API_BASE_URL=https://your-api-domain`

## Why I Recommend This Split

The dashboard is a frontend app and Vercel is very good for that.

The backend handles:

- auth
- agent ingestion
- response actions
- database access

That part is usually better on a dedicated backend platform.

## Official Vercel Notes

Vercel officially supports FastAPI, but it runs as a Vercel Function and function limits apply.

Sources:

- [FastAPI on Vercel](https://vercel.com/docs/frameworks/backend/fastapi)
- [Vercel Functions Limits](https://vercel.com/docs/functions/limitations)
- [Vite on Vercel](https://vercel.com/docs/frameworks/frontend/vite)

## Frontend Deployment To Vercel

### Option A: Deploy from the `dashboard` folder

Best option.

In Vercel:

1. Import your Git repository
2. Set the project root to:
   - `dashboard`
3. Framework preset:
   - `Vite`
4. Build command:
   - `npm run build`
5. Output directory:
   - `dist`

### Required Environment Variable

Set this in Vercel:

- `VITE_API_BASE_URL=https://your-backend-domain`

Example:

- `VITE_API_BASE_URL=https://api.yourcompany.com`

## Files Added For Vercel Frontend Deploy

- `dashboard/vercel.json`

This keeps client-side routes working for the dashboard app.

## If You Still Want Backend On Vercel

It is possible in principle, but for this product I do **not** recommend it as the main production plan.

Reasons:

- function limits still apply
- serverless behavior is less ideal for this kind of security product
- database and agent-ingestion workflows are usually better on a dedicated backend host

## Local Reminder

Vercel will only give you the hosted dashboard domain if you deploy the frontend there.

The employee agent does **not** get deployed to Vercel.
You distribute the agent separately to customer devices.
