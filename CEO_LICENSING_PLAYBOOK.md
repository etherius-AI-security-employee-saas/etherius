# CEO Licensing Playbook

## Goal
You (CEO) issue subscription keys to each customer company admin.  
Customer admin then creates employee keys inside dashboard.

## Step 1: Set CEO master key
In `backend/.env`:
```env
CEO_MASTER_KEY=YOUR_LONG_RANDOM_SECRET_KEY
```
Restart backend.

## Step 2: Issue a customer subscription key
Use Swagger:
- Open `http://localhost:8000/docs`
- Find `POST /api/licenses/subscription/issue`
- Header:
  - `X-CEO-Key: YOUR_LONG_RANDOM_SECRET_KEY`
- Body example:
```json
{
  "label": "Acme Corp - Annual",
  "max_activations": 1,
  "valid_days": 365
}
```

Response includes `key_value` like `ETH-SUB-XXXXX-XXXXX-XXXXX`.

## Step 3: Send this to customer admin
Send:
1. Installer package (`Etherius-Setup.exe` after build)
2. Their subscription key
3. Admin onboarding PDF/guide

## Step 4: Customer admin flow
1. Install Etherius.
2. Register company in dashboard using subscription key.
3. Create employee license keys from Settings.
4. Share employee key + enrollment code to their employees.

## Step 5: Employee flow
1. Run Etherius Shield.
2. Paste enrollment code + employee license key.
3. Click Enroll and Start Protection.
