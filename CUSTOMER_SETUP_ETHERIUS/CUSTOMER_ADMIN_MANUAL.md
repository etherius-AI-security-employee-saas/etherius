# Customer Admin Manual (Simple)

Use this if you are the customer administrator.

## 1) Start the software

1. Open the `admin` folder.
2. Double-click `ADMIN_START_ETHERIUS.bat`.
3. Wait for dashboard to open.

If browser does not auto-open, open:
- `http://localhost:8000/dashboard`

## 2) Register your company (first time only)

1. Click **Register Company**.
2. Enter:
- Company name
- Your admin name
- Your admin email
- Password
- Subscription key (provided by provider)
3. Submit and log in.

## 3) Daily login

1. Open dashboard.
2. Sign in with your admin email and password.

## 4) Generate employee access keys

1. Go to **Settings**.
2. In employee key section, click **Generate Employee Key**.
3. Set:
- Label (optional)
- Max activations
- Valid days
4. Copy the generated key.

## 5) Give onboarding info to each employee

Send employee:

1. Company Enrollment Code (shown in your Settings/account area)
2. Employee Key
3. Backend URL (if your provider gave a domain URL)

## 6) Add/track employees

1. Go to **Endpoints/Employees** page.
2. Confirm enrolled devices appear online.
3. Revoke employee keys in Settings if needed.

## 7) Seat limit behavior

- Your subscription has a fixed employee quantity (example: 300).
- After limit is reached, new enrollments are blocked.
- Contact provider to increase seats.

## 8) Security rules

1. Do not share admin password with employees.
2. Do not share all keys in public chat/email.
3. Revoke old keys for retired devices.

## 9) Troubleshooting

If dashboard not loading:

1. Re-run `ADMIN_START_ETHERIUS.bat`
2. Check backend is running on port 8000
3. Try `http://localhost:8000/health`

If employee cannot enroll:

1. Re-check enrollment code
2. Re-check employee key
3. Confirm seat limit not exceeded
4. Confirm backend URL is correct
