import ctypes
import json
import os
import platform
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

import requests

from agent.core.agent import EtheriusAgent
from agent.core.client import send_event
from agent.core.config import get_config, update_config
from agent.core.device_info import collect_device_info
from agent.core.local_scanner import run_threat_scan


DEFAULT_API_URL = os.getenv("ETHERIUS_API_URL", "https://etherius-security-api.vercel.app")
ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "suite" / "assets"


def resolve_state_file() -> Path:
    if getattr(__import__("sys"), "frozen", False):
        import sys

        return Path(sys.executable).resolve().parent / "suite_state.json"
    return ROOT / "suite" / "suite_state.json"


class EtheriusApp:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("Etherius Unified Security")
        self.root.geometry("1280x860")
        self.root.minsize(1080, 760)
        self.root.configure(bg="#070612")
        self.icon_image = None
        self.state_file = resolve_state_file()
        self.state = self._load_state()

        self.access_token = ""
        self.admin_role = ""
        self.admin_name = ""

        self.agent = EtheriusAgent(on_status=self._on_agent_status, on_event=self._on_agent_event)

        self.backend_url_var = tk.StringVar(value=self.state.get("backend_url", DEFAULT_API_URL))
        self.admin_email_var = tk.StringVar(value=self.state.get("admin_email", ""))
        self.admin_password_var = tk.StringVar(value="")
        self.admin_company_name_var = tk.StringVar(value=self.state.get("company_name", ""))
        self.admin_company_domain_var = tk.StringVar(value=self.state.get("company_domain", ""))
        self.admin_full_name_var = tk.StringVar(value=self.state.get("admin_full_name", ""))
        self.subscription_key_var = tk.StringVar(value="")

        self.employee_company_code_var = tk.StringVar(value=self.state.get("employee_company_code", ""))
        self.employee_key_var = tk.StringVar(value=self.state.get("employee_key", ""))
        self.employee_activation_var = tk.StringVar(value=self.state.get("activation_code", ""))
        self.employee_endpoint_id_var = tk.StringVar(value=self.state.get("endpoint_id", ""))
        self.employee_token_var = tk.StringVar(value=self.state.get("agent_token", ""))

        self.stats_text_var = tk.StringVar(value="Dashboard locked. Activate or sign in as customer admin.")
        self.company_code_var = tk.StringVar(value="-")
        self.subscription_status_var = tk.StringVar(value="-")
        self.subscription_seats_var = tk.StringVar(value="-")
        self.subscription_capacity_var = tk.StringVar(value="-")
        self.admin_session_var = tk.StringVar(value="Not signed in")
        self.employee_runtime_var = tk.StringVar(value="Protection offline")
        self.employee_heartbeat_var = tk.StringVar(value="Heartbeat: waiting")
        self.employee_events_var = tk.StringVar(value="Events: 0 sent, 0 failed")
        self.scan_summary_var = tk.StringVar(value="Scan not started.")

        self.employee_key_label_var = tk.StringVar(value="")
        self.employee_key_max_var = tk.StringVar(value="1")
        self.employee_key_days_var = tk.StringVar(value="365")

        self.endpoints_list = None
        self.alerts_list = None
        self.employee_keys_list = None
        self.activity_feed = None
        self.scan_results = None

        self._set_identity()
        self._configure_styles()
        self._build()
        self._load_agent_config_to_ui()
        self._set_admin_unlocked(False)
        self._append_feed("Etherius started in unified mode.")
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _set_identity(self):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Etherius.Unified")
        except Exception:
            pass

        ico_path = ASSETS / "etherius-suite.ico"
        png_path = ASSETS / "etherius-suite.png"
        try:
            if ico_path.exists():
                self.root.iconbitmap(default=str(ico_path))
        except Exception:
            pass
        try:
            if png_path.exists():
                self.icon_image = tk.PhotoImage(file=str(png_path))
                self.root.iconphoto(True, self.icon_image)
        except Exception:
            pass

    def _configure_styles(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("Primary.TButton", padding=(12, 8), font=("Segoe UI", 10, "bold"))
        style.configure("Secondary.TButton", padding=(10, 7), font=("Segoe UI", 10))
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#f5f0ff", background="#070612")
        style.configure("Muted.TLabel", font=("Segoe UI", 10), foreground="#bfb5e0", background="#070612")

    def _build(self):
        shell = tk.Frame(self.root, bg="#070612")
        shell.pack(fill="both", expand=True, padx=18, pady=14)

        top = tk.Frame(shell, bg="#070612")
        top.pack(fill="x", pady=(0, 10))
        ttk.Label(top, text="Etherius Unified Security Console", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            top,
            text="One software for customer admin activation, employee onboarding, and endpoint protection.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        notebook = ttk.Notebook(shell)
        notebook.pack(fill="both", expand=True)

        admin_tab = tk.Frame(notebook, bg="#0f0c22")
        employee_tab = tk.Frame(notebook, bg="#0f0c22")
        ops_tab = tk.Frame(notebook, bg="#0f0c22")
        notebook.add(admin_tab, text="Admin Activation + Dashboard")
        notebook.add(employee_tab, text="Employee Activation + Protection")
        notebook.add(ops_tab, text="Operations")

        self._build_admin_tab(admin_tab)
        self._build_employee_tab(employee_tab)
        self._build_ops_tab(ops_tab)

    def _build_admin_tab(self, parent):
        wrap = tk.Frame(parent, bg="#0f0c22")
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        conn = tk.LabelFrame(wrap, text="Connection", bg="#151132", fg="#f2eaff", bd=1, relief="groove")
        conn.pack(fill="x", pady=(0, 10))
        self._labeled_entry(conn, "API URL", self.backend_url_var, width=76).pack(fill="x", padx=10, pady=8)

        auth_row = tk.Frame(wrap, bg="#0f0c22")
        auth_row.pack(fill="x", pady=(0, 10))

        activation_box = tk.LabelFrame(
            auth_row,
            text="New Customer Activation (requires subscription license key)",
            bg="#151132",
            fg="#f2eaff",
            bd=1,
            relief="groove",
        )
        activation_box.pack(side="left", fill="both", expand=True, padx=(0, 6))

        self._labeled_entry(activation_box, "Company Name", self.admin_company_name_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(activation_box, "Company Domain", self.admin_company_domain_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(activation_box, "Admin Full Name", self.admin_full_name_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(activation_box, "Admin Email", self.admin_email_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(activation_box, "Admin Password", self.admin_password_var, show="*").pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(activation_box, "Subscription License Key", self.subscription_key_var).pack(fill="x", padx=10, pady=(8, 0))
        ttk.Button(activation_box, text="Activate Company", style="Primary.TButton", command=self.activate_company).pack(
            anchor="e", padx=10, pady=10
        )

        signin_box = tk.LabelFrame(
            auth_row,
            text="Existing Customer Admin Sign In",
            bg="#151132",
            fg="#f2eaff",
            bd=1,
            relief="groove",
        )
        signin_box.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._labeled_entry(signin_box, "Admin Email", self.admin_email_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(signin_box, "Admin Password", self.admin_password_var, show="*").pack(fill="x", padx=10, pady=(8, 0))
        btn_row = tk.Frame(signin_box, bg="#151132")
        btn_row.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_row, text="Sign In", style="Primary.TButton", command=self.sign_in_admin).pack(side="left")
        ttk.Button(btn_row, text="Sign Out", style="Secondary.TButton", command=self.sign_out_admin).pack(side="left", padx=8)
        ttk.Button(btn_row, text="Refresh Dashboard", style="Secondary.TButton", command=self.refresh_admin_dashboard).pack(side="left")

        tk.Label(signin_box, textvariable=self.admin_session_var, bg="#151132", fg="#8de4be", anchor="w").pack(fill="x", padx=10, pady=(2, 10))

        dashboard = tk.LabelFrame(wrap, text="In-App Customer Dashboard", bg="#151132", fg="#f2eaff", bd=1, relief="groove")
        dashboard.pack(fill="both", expand=True)
        self.admin_locked_overlay = tk.Label(
            dashboard,
            text="Locked. Activate company with subscription key or sign in as admin customer.",
            bg="#201a45",
            fg="#ffd7a8",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=6,
        )
        self.admin_locked_overlay.pack(fill="x", padx=10, pady=(8, 6))

        summary = tk.Frame(dashboard, bg="#151132")
        summary.pack(fill="x", padx=10, pady=(0, 6))
        tk.Label(summary, textvariable=self.stats_text_var, bg="#151132", fg="#e9e3ff", justify="left", anchor="w").pack(fill="x")
        tk.Label(summary, textvariable=self.company_code_var, bg="#151132", fg="#9dd8ff", anchor="w").pack(fill="x", pady=(2, 0))
        tk.Label(summary, textvariable=self.subscription_status_var, bg="#151132", fg="#a9f3d0", anchor="w").pack(fill="x")
        tk.Label(summary, textvariable=self.subscription_seats_var, bg="#151132", fg="#a9f3d0", anchor="w").pack(fill="x")
        tk.Label(summary, textvariable=self.subscription_capacity_var, bg="#151132", fg="#a9f3d0", anchor="w").pack(fill="x")

        grid = tk.Frame(dashboard, bg="#151132")
        grid.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        endpoints_box = tk.LabelFrame(grid, text="Employees / Endpoints", bg="#151132", fg="#f2eaff")
        endpoints_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        self.endpoints_list = tk.Listbox(endpoints_box, height=12, bg="#0c0a1d", fg="#e7ddff")
        self.endpoints_list.pack(fill="both", expand=True, padx=8, pady=8)

        alerts_box = tk.LabelFrame(grid, text="Open Alerts", bg="#151132", fg="#f2eaff")
        alerts_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))
        self.alerts_list = tk.Listbox(alerts_box, height=12, bg="#0c0a1d", fg="#ffd9b3")
        self.alerts_list.pack(fill="both", expand=True, padx=8, pady=8)

        keys_box = tk.LabelFrame(grid, text="Employee Activation Keys", bg="#151132", fg="#f2eaff")
        keys_box.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        key_form = tk.Frame(keys_box, bg="#151132")
        key_form.pack(fill="x", padx=8, pady=8)
        self._labeled_entry(key_form, "Label", self.employee_key_label_var, width=26).grid(row=0, column=0, padx=(0, 8))
        self._labeled_entry(key_form, "Max Activations", self.employee_key_max_var, width=14).grid(row=0, column=1, padx=(0, 8))
        self._labeled_entry(key_form, "Valid Days", self.employee_key_days_var, width=14).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(key_form, text="Generate Employee Key", style="Primary.TButton", command=self.create_employee_key).grid(row=0, column=3)

        self.employee_keys_list = tk.Listbox(keys_box, height=8, bg="#0c0a1d", fg="#e7ddff")
        self.employee_keys_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)
    def _build_employee_tab(self, parent):
        wrap = tk.Frame(parent, bg="#0f0c22")
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        setup = tk.LabelFrame(wrap, text="Employee Activation (same software)", bg="#151132", fg="#f2eaff", bd=1, relief="groove")
        setup.pack(fill="x", pady=(0, 10))
        self._labeled_entry(setup, "API URL", self.backend_url_var, width=76).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(setup, "Company Enrollment Code", self.employee_company_code_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(setup, "Employee Activation Key", self.employee_key_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(setup, "Activation Code", self.employee_activation_var).pack(fill="x", padx=10, pady=(8, 0))

        btn_row = tk.Frame(setup, bg="#151132")
        btn_row.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_row, text="Enroll Employee Device", style="Primary.TButton", command=self.enroll_employee_device).pack(side="left")
        ttk.Button(btn_row, text="Apply Activation Code", style="Secondary.TButton", command=self.apply_activation_code).pack(side="left", padx=8)
        ttk.Button(btn_row, text="Start Protection", style="Primary.TButton", command=self.start_protection).pack(side="left", padx=8)
        ttk.Button(btn_row, text="Stop Protection", style="Secondary.TButton", command=self.stop_protection).pack(side="left")

        scan_row = tk.Frame(setup, bg="#151132")
        scan_row.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(scan_row, text="Quick AI Threat Scan", style="Secondary.TButton", command=self.run_quick_scan).pack(side="left")
        ttk.Button(scan_row, text="Deep Corporate Risk Scan", style="Secondary.TButton", command=self.run_deep_scan).pack(side="left", padx=8)
        tk.Label(scan_row, textvariable=self.scan_summary_var, bg="#151132", fg="#ffd59f", anchor="w").pack(side="left", padx=10)

        tk.Label(setup, textvariable=self.employee_runtime_var, bg="#151132", fg="#8de4be", anchor="w").pack(fill="x", padx=10)
        tk.Label(setup, textvariable=self.employee_heartbeat_var, bg="#151132", fg="#c6bbeb", anchor="w").pack(fill="x", padx=10)
        tk.Label(setup, textvariable=self.employee_events_var, bg="#151132", fg="#c6bbeb", anchor="w").pack(fill="x", padx=10, pady=(0, 8))

        details = tk.Frame(wrap, bg="#0f0c22")
        details.pack(fill="both", expand=True)

        left = tk.LabelFrame(details, text="Device Identity", bg="#151132", fg="#f2eaff")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.LabelFrame(details, text="Protection Activity Feed", bg="#151132", fg="#f2eaff")
        right.pack(side="left", fill="both", expand=True, padx=(6, 0))

        info = collect_device_info()
        device_lines = [
            f"Hostname: {info.get('hostname', '-')}",
            f"OS: {info.get('os', '-')}",
            f"IP: {info.get('ip_address', '-')}",
            f"MAC: {info.get('mac_address', '-')}",
            f"User: {info.get('device_user', '-')}",
            f"Platform: {platform.platform()}",
        ]
        for line in device_lines:
            tk.Label(left, text=line, bg="#151132", fg="#e7ddff", anchor="w").pack(fill="x", padx=10, pady=(8, 0))

        self.activity_feed = tk.Text(right, bg="#0c0a1d", fg="#daceff", relief="flat")
        self.activity_feed.pack(fill="both", expand=True, padx=8, pady=8)

        self.scan_results = tk.Text(left, height=10, bg="#0c0a1d", fg="#9dd8ff", relief="flat")
        self.scan_results.pack(fill="both", expand=True, padx=10, pady=(10, 10))

    def _build_ops_tab(self, parent):
        wrap = tk.Frame(parent, bg="#0f0c22")
        wrap.pack(fill="both", expand=True, padx=14, pady=14)
        box = tk.LabelFrame(wrap, text="Platform Notes", bg="#151132", fg="#f2eaff")
        box.pack(fill="both", expand=True)

        lines = [
            "1) One setup and one app now handles both customer admin and employee activation.",
            "2) Customer admin dashboard is inside this software and is locked until activation/sign-in.",
            "3) Company activation requires a valid subscription license key from CEO/provider.",
            "4) Employee keys are generated by customer admin with seat-limit enforcement.",
            "5) Employees use this same app in Employee Activation tab to enroll and start protection.",
            "6) Endpoint telemetry and risk alerts are sent to backend and shown in the in-app dashboard.",
        ]
        for line in lines:
            tk.Label(box, text=line, bg="#151132", fg="#e7ddff", justify="left", anchor="w").pack(fill="x", padx=12, pady=(10, 0))

    def _labeled_entry(self, parent, label, variable, width=34, show=None):
        frame = tk.Frame(parent, bg=parent["bg"])
        tk.Label(frame, text=label, bg=parent["bg"], fg="#c9bfe8", anchor="w").pack(anchor="w")
        tk.Entry(frame, textvariable=variable, width=width, show=show, bg="#0c0a1d", fg="#efe9ff", insertbackground="#efe9ff").pack(fill="x", pady=(3, 0))
        return frame

    def _request(self, method, path, payload=None, auth=False, timeout=20):
        base = self.backend_url_var.get().strip().rstrip("/")
        if not base:
            raise RuntimeError("API URL is required")
        url = f"{base}{path}"
        headers = {}
        if auth and self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        response = requests.request(method=method, url=url, json=payload, headers=headers, timeout=timeout)
        if response.status_code >= 400:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            raise RuntimeError(f"{response.status_code}: {detail}")
        if response.content:
            return response.json()
        return {}

    def activate_company(self):
        payload = {
            "company_name": self.admin_company_name_var.get().strip(),
            "domain": self.admin_company_domain_var.get().strip() or None,
            "admin_email": self.admin_email_var.get().strip(),
            "admin_password": self.admin_password_var.get().strip(),
            "admin_full_name": self.admin_full_name_var.get().strip(),
            "subscription_key": self.subscription_key_var.get().strip(),
        }
        missing = [k for k, v in payload.items() if k != "domain" and not v]
        if missing:
            messagebox.showerror("Missing data", "Fill all activation fields, including subscription license key.")
            return
        try:
            self._request("POST", "/api/auth/register", payload=payload, auth=False)
            self.sign_in_admin(show_success=False)
            self._append_feed("Company activated with subscription license key.")
            messagebox.showinfo("Activated", "Company activation successful. Dashboard unlocked.")
        except Exception as error:
            messagebox.showerror("Activation failed", str(error))

    def sign_in_admin(self, show_success=True):
        payload = {
            "email": self.admin_email_var.get().strip(),
            "password": self.admin_password_var.get().strip(),
        }
        if not payload["email"] or not payload["password"]:
            messagebox.showerror("Missing credentials", "Enter admin email and password.")
            return
        try:
            data = self._request("POST", "/api/auth/login", payload=payload, auth=False)
            role = str(data.get("role", "")).lower()
            if role not in {"manager", "admin", "superadmin"}:
                raise RuntimeError("This account cannot access manager dashboard.")
            self.access_token = data["access_token"]
            self.admin_role = role
            self.admin_name = data.get("full_name") or payload["email"]
            self.admin_session_var.set(f"Signed in as {self.admin_name} ({self.admin_role})")
            self._set_admin_unlocked(True)
            self.refresh_admin_dashboard()
            if show_success:
                messagebox.showinfo("Signed in", "Admin dashboard is now unlocked in this software.")
            self._append_feed("Admin signed in and dashboard unlocked.")
        except Exception as error:
            self._set_admin_unlocked(False)
            messagebox.showerror("Sign in failed", str(error))

    def sign_out_admin(self):
        self.access_token = ""
        self.admin_role = ""
        self.admin_name = ""
        self.admin_session_var.set("Not signed in")
        self._set_admin_unlocked(False)
        self.stats_text_var.set("Dashboard locked. Activate or sign in as customer admin.")
        self.company_code_var.set("-")
        self.subscription_status_var.set("-")
        self.subscription_seats_var.set("-")
        self.subscription_capacity_var.set("-")
        self._clear_list(self.endpoints_list)
        self._clear_list(self.alerts_list)
        self._clear_list(self.employee_keys_list)
        self._append_feed("Admin signed out.")
    def refresh_admin_dashboard(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in first to access dashboard.")
            return
        try:
            stats = self._request("GET", "/api/dashboard/stats", auth=True)
            endpoints = self._request("GET", "/api/dashboard/endpoints", auth=True)
            alerts = self._request("GET", "/api/dashboard/alerts?status=open&limit=20", auth=True)
            subscription = self._request("GET", "/api/licenses/subscription", auth=True)
            keys = self._request("GET", "/api/licenses/employee", auth=True)
            me = self._request("GET", "/api/auth/me", auth=True)
        except Exception as error:
            messagebox.showerror("Refresh failed", str(error))
            return

        summary = (
            f"Endpoints: {stats.get('total_endpoints', 0)} total / {stats.get('online_endpoints', 0)} online  |  "
            f"Open alerts: {stats.get('open_alerts', 0)}  |  Critical: {stats.get('critical_alerts', 0)}  |  "
            f"Logins today: {stats.get('login_events_today', 0)}  |  Logouts today: {stats.get('logout_events_today', 0)}"
        )
        self.stats_text_var.set(summary)
        self.company_code_var.set(f"Company Enrollment Code: {me.get('company_code', '-')}")
        self.subscription_status_var.set(
            f"Subscription: {subscription.get('status', 'unknown')}  |  Active: {subscription.get('is_active', False)}"
        )
        self.subscription_seats_var.set(
            f"Employee seats in use: {subscription.get('employees_used', 0)} / {subscription.get('employee_limit', 0)}"
        )
        self.subscription_capacity_var.set(
            f"Employee key capacity allocated: {subscription.get('employee_key_capacity_allocated', 0)} / {subscription.get('employee_limit', 0)}"
        )

        self._clear_list(self.endpoints_list)
        for endpoint in endpoints:
            line = f"{endpoint.get('hostname', '-'):<24} | {endpoint.get('status', '-'):<8} | risk {endpoint.get('risk_score', '0')}"
            self.endpoints_list.insert("end", line)
        if not endpoints:
            self.endpoints_list.insert("end", "No endpoints connected yet.")

        self._clear_list(self.alerts_list)
        for alert in alerts:
            line = f"[{alert.get('severity', 'info').upper()}] {alert.get('title', '-')}"
            self.alerts_list.insert("end", line)
        if not alerts:
            self.alerts_list.insert("end", "No open alerts.")

        self._clear_list(self.employee_keys_list)
        for key in keys:
            line = (
                f"{key.get('key_value', '-')}"
                f" | used {key.get('current_activations', 0)}/{key.get('max_activations', 0)}"
                f" | active={key.get('is_active', False)}"
            )
            self.employee_keys_list.insert("end", line)
        if not keys:
            self.employee_keys_list.insert("end", "No employee activation keys generated.")

        self._append_feed("Admin dashboard data refreshed.")

    def create_employee_key(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as customer admin first.")
            return
        try:
            max_activations = int(self.employee_key_max_var.get().strip() or "1")
            valid_days = int(self.employee_key_days_var.get().strip() or "365")
        except ValueError:
            messagebox.showerror("Invalid input", "Max activations and valid days must be numbers.")
            return

        payload = {
            "label": self.employee_key_label_var.get().strip() or None,
            "max_activations": max_activations,
            "valid_days": valid_days,
        }
        try:
            key = self._request("POST", "/api/licenses/employee", payload=payload, auth=True)
            self._append_feed(f"Generated employee key: {key.get('key_value', '-')}")
            self.employee_key_var.set(key.get("key_value", ""))
            self.refresh_admin_dashboard()
        except Exception as error:
            messagebox.showerror("Key generation failed", str(error))

    def enroll_employee_device(self):
        company_code = self.employee_company_code_var.get().strip()
        employee_key = self.employee_key_var.get().strip()
        if not company_code or not employee_key:
            messagebox.showerror("Missing input", "Enter company enrollment code and employee activation key.")
            return

        payload = collect_device_info()
        payload["company_code"] = company_code
        payload["employee_key"] = employee_key

        try:
            data = self._request("POST", "/api/agent/enroll", payload=payload, auth=False)
            activation_code = data.get("activation_code", "")
            self.employee_activation_var.set(activation_code)
            self.apply_activation_code(show_message=False)
            self._append_feed("Employee device enrolled successfully.")
            messagebox.showinfo("Enrolled", "Employee device enrolled. You can now start protection.")
        except Exception as error:
            messagebox.showerror("Enrollment failed", str(error))

    def apply_activation_code(self, show_message=True):
        code = self.employee_activation_var.get().strip()
        parts = code.split("|")
        if len(parts) != 3:
            if show_message:
                messagebox.showerror("Invalid code", "Activation code format is backend_url|endpoint_id|agent_token")
            return
        backend_url, endpoint_id, agent_token = parts
        self.backend_url_var.set(backend_url)
        self.employee_endpoint_id_var.set(endpoint_id)
        self.employee_token_var.set(agent_token)
        update_config(
            {
                "backend_url": backend_url,
                "company_code": self.employee_company_code_var.get().strip(),
                "employee_key": self.employee_key_var.get().strip(),
                "activation_code": code,
                "endpoint_id": endpoint_id,
                "agent_token": agent_token,
            }
        )
        if show_message:
            messagebox.showinfo("Applied", "Activation code applied.")
        self._append_feed("Activation code applied to local agent config.")

    def start_protection(self):
        if not self.employee_token_var.get().strip() or not self.employee_endpoint_id_var.get().strip():
            self.apply_activation_code(show_message=False)
        if not self.employee_token_var.get().strip() or not self.employee_endpoint_id_var.get().strip():
            messagebox.showerror("Missing activation", "Enroll first or apply a valid activation code.")
            return

        update_config(
            {
                "backend_url": self.backend_url_var.get().strip(),
                "company_code": self.employee_company_code_var.get().strip(),
                "employee_key": self.employee_key_var.get().strip(),
                "activation_code": self.employee_activation_var.get().strip(),
                "endpoint_id": self.employee_endpoint_id_var.get().strip(),
                "agent_token": self.employee_token_var.get().strip(),
            }
        )
        self.agent.start()
        self.employee_runtime_var.set("Protection active")
        self._append_feed("Protection started.")

    def stop_protection(self):
        self.agent.stop()
        self.employee_runtime_var.set("Protection offline")
        self._append_feed("Protection stopped.")

    def run_quick_scan(self):
        self._run_local_scan(deep=False)

    def run_deep_scan(self):
        self._run_local_scan(deep=True)

    def _run_local_scan(self, deep=False):
        try:
            scan_data = run_threat_scan(deep=deep)
            summary = scan_data["summary"]
            findings = scan_data["findings"]
            self.scan_summary_var.set(
                f"{summary['mode'].upper()} scan: {summary['local_scan_severity']} ({summary['local_scan_risk_score']}/100), findings={summary['suspicious_items_found']}"
            )
            self._render_scan_results(summary, findings)
            self._append_feed(f"{summary['mode'].upper()} scan completed with risk {summary['local_scan_risk_score']}.")

            event_payload = {
                **summary,
                "findings_preview": {
                    "process_hits": findings.get("process_hits", [])[:5],
                    "network_hits": findings.get("network_hits", [])[:5],
                    "filesystem_hits": findings.get("filesystem_hits", [])[:5],
                },
            }

            # Advisory-only by design: scan reports and alerts, but does not auto-block business operations.
            self._send_scan_event(event_payload)
        except Exception as error:
            messagebox.showerror("Scan failed", str(error))

    def _send_scan_event(self, payload):
        if not self.employee_token_var.get().strip():
            self._append_feed("Scan event not sent: device not activated yet.")
            return
        try:
            update_config(
                {
                    "backend_url": self.backend_url_var.get().strip(),
                    "endpoint_id": self.employee_endpoint_id_var.get().strip(),
                    "agent_token": self.employee_token_var.get().strip(),
                }
            )
            send_event({"event_type": "threat_scan", "severity": "info", "payload": payload}, timeout=20)
            self._append_feed("Scan event sent to manager dashboard.")
        except Exception as error:
            self._append_feed(f"Scan event send failed: {error}")

    def _render_scan_results(self, summary, findings):
        if not self.scan_results:
            return
        self.scan_results.delete("1.0", "end")
        lines = [
            f"Mode: {summary.get('mode', '-')}",
            f"Risk: {summary.get('local_scan_risk_score', 0)}/100 ({summary.get('local_scan_severity', '-')})",
            f"Suspicious items: {summary.get('suspicious_items_found', 0)}",
            f"Processes checked: {summary.get('processes_checked', 0)}",
            f"Connections checked: {summary.get('network_connections_checked', 0)}",
            f"Allowlisted safe activities skipped: {summary.get('safe_process_allowlist_hits', 0)}",
            "",
            "Top Findings:",
        ]

        for group_name, items in [
            ("Process", findings.get("process_hits", [])),
            ("Network", findings.get("network_hits", [])),
            ("Filesystem", findings.get("filesystem_hits", [])),
        ]:
            if not items:
                continue
            for item in items[:5]:
                reason = item.get("reason", "Suspicious behavior detected")
                target = item.get("name") or item.get("remote") or item.get("path") or "unknown"
                lines.append(f"- [{group_name}] {target} | {reason}")

        if len(lines) <= 8:
            lines.append("- No high-confidence suspicious artifacts found in this scan.")

        self.scan_results.insert("end", "\n".join(lines))
    def _on_agent_status(self, status):
        self.root.after(0, lambda: self._update_agent_status(status))

    def _on_agent_event(self, item):
        self.root.after(0, lambda: self._append_feed(self._format_agent_event(item)))

    def _update_agent_status(self, status):
        hb = "connected" if status.get("heartbeat_ok") else "waiting"
        self.employee_heartbeat_var.set(f"Heartbeat: {hb}")
        self.employee_events_var.set(
            f"Events: {status.get('events_sent', 0)} sent, {status.get('events_failed', 0)} failed"
        )

    def _format_agent_event(self, item):
        kind = item.get("kind", "event").upper()
        event_type = item.get("event_type", "unknown")
        detail = item.get("error") or item.get("status_code") or ""
        return f"{kind} | {event_type} {detail}".strip()

    def _append_feed(self, text):
        if not self.activity_feed:
            return
        stamp = datetime.now().strftime("%H:%M:%S")
        self.activity_feed.insert("end", f"[{stamp}] {text}\n")
        self.activity_feed.see("end")

    def _set_admin_unlocked(self, unlocked: bool):
        self.admin_locked_overlay.configure(
            text="Dashboard unlocked in software." if unlocked else "Locked. Activate company with subscription key or sign in as admin customer.",
            fg="#8de4be" if unlocked else "#ffd7a8",
        )

    def _clear_list(self, listbox):
        if listbox:
            listbox.delete(0, "end")

    def _load_agent_config_to_ui(self):
        cfg = get_config()
        self.backend_url_var.set(cfg.get("backend_url") or self.backend_url_var.get())
        self.employee_company_code_var.set(cfg.get("company_code", self.employee_company_code_var.get()))
        self.employee_key_var.set(cfg.get("employee_key", self.employee_key_var.get()))
        self.employee_activation_var.set(cfg.get("activation_code", self.employee_activation_var.get()))
        self.employee_endpoint_id_var.set(cfg.get("endpoint_id", self.employee_endpoint_id_var.get()))
        self.employee_token_var.set(cfg.get("agent_token", self.employee_token_var.get()))

    def _load_state(self):
        if not self.state_file.exists():
            return {}
        try:
            return json.loads(self.state_file.read_text(encoding="utf-8"))
        except Exception:
            return {}

    def _save_state(self):
        data = {
            "backend_url": self.backend_url_var.get().strip(),
            "admin_email": self.admin_email_var.get().strip(),
            "company_name": self.admin_company_name_var.get().strip(),
            "company_domain": self.admin_company_domain_var.get().strip(),
            "admin_full_name": self.admin_full_name_var.get().strip(),
            "employee_company_code": self.employee_company_code_var.get().strip(),
            "employee_key": self.employee_key_var.get().strip(),
            "activation_code": self.employee_activation_var.get().strip(),
            "endpoint_id": self.employee_endpoint_id_var.get().strip(),
            "agent_token": self.employee_token_var.get().strip(),
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _on_close(self):
        try:
            self.agent.stop()
        except Exception:
            pass
        try:
            self._save_state()
        except Exception:
            pass
        self.root.destroy()


def main():
    root = tk.Tk()
    EtheriusApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
