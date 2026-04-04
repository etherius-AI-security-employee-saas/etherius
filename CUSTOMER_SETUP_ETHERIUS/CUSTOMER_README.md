# Etherius Customer Quick Start

This folder is the customer software package.  
No source code is required.

## Folder Contents

- `admin/` = Customer admin software
- `employee/` = Employee protection software
- `CUSTOMER_ADMIN_MANUAL.md` = Full admin steps
- `EMPLOYEE_MANUAL.md` = Full employee steps

## Who Uses What

1. Customer admin uses files in `admin/`
2. Employees use files in `employee/`

## First Launch Order

1. Customer admin runs `admin\ADMIN_START_ETHERIUS.bat`
2. Customer admin registers/logs in and creates employee keys
3. Employee installs and runs `employee\EMPLOYEE_START_SHIELD.bat`
4. Employee enters:
- Company Enrollment Code (from admin)
- Employee Key (from admin)
- Backend URL (from admin, if needed)

## Important

- Customer admin should not share admin login with employees.
- Employee users do not need dashboard access.
- If backend is hosted on a domain, employees use that domain URL.
