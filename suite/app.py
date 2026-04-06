import ctypes
import json
import os
import platform
import random
import sys
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

import requests

from agent.core.agent import EtheriusAgent
from agent.core.client import send_event
from agent.core.config import get_config, update_config
from agent.core.device_info import collect_device_info
from agent.core.local_scanner import run_threat_scan


DEFAULT_API_URL = os.getenv("ETHERIUS_API_URL", "https://etherius-security-api.vercel.app")
ROOT = Path(__file__).resolve().parent.parent


def resolve_assets_dir() -> Path:
    candidates = []
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", "")
        if meipass:
            candidates.append(Path(meipass) / "suite" / "assets")
        candidates.append(Path(sys.executable).resolve().parent / "_internal" / "suite" / "assets")
        candidates.append(Path(sys.executable).resolve().parent / "suite" / "assets")
    candidates.append(ROOT / "suite" / "assets")
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return ROOT / "suite" / "assets"


ASSETS = resolve_assets_dir()


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
        self.root.configure(bg="#060814")
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
        self.posture_score_var = tk.StringVar(value="Protection posture: baseline")
        self.endpoint_health_var = tk.StringVar(value="Endpoint health: waiting")
        self.live_sync_state_var = tk.StringVar(value="Cloud sync: idle")
        self.alert_mode_var = tk.StringVar(value="Alert mode: balanced")

        self.employee_key_label_var = tk.StringVar(value="")
        self.employee_key_max_var = tk.StringVar(value="1")
        self.employee_key_days_var = tk.StringVar(value="365")

        self.endpoints_list = None
        self.alerts_list = None
        self.employee_keys_list = None
        self.activity_feed = None
        self.scan_results = None
        self.notebook = None
        self.admin_tab = None
        self.employee_tab = None
        self.ops_tab = None
        self.admin_tab_visible = True
        self.auto_scan_job = None
        self.admin_live_job = None
        self.scan_running = False
        self.endpoint_selector = None
        self.endpoint_selector_var = tk.StringVar(value="")
        self.remote_message_var = tk.StringVar(value="")
        self.usb_policy_var = tk.StringVar(value="allow_all")
        self.usb_device_id_var = tk.StringVar(value="")
        self.usb_device_name_var = tk.StringVar(value="")
        self.app_name_var = tk.StringVar(value="")
        self.app_action_var = tk.StringVar(value="kill")
        self.domain_var = tk.StringVar(value="")
        self.domain_category_var = tk.StringVar(value="custom")
        self.report_days_var = tk.StringVar(value="30")
        self.compliance_score_var = tk.StringVar(value="-")
        self.command_history_list = None
        self.usb_devices_list = None
        self.app_blacklist_list = None
        self.domain_list = None
        self.insider_list = None
        self.vuln_list = None
        self.report_summary_text = None
        self.endpoint_lookup = {}

        self.policy_mode_var = tk.StringVar(value=str(self.state.get("policy_mode", "advisory")))
        self.ai_sensitivity_var = tk.IntVar(value=self._safe_int(self.state.get("ai_sensitivity", 70), 70))
        self.auto_scan_interval_var = tk.StringVar(value=str(self.state.get("auto_scan_interval", "30")))
        self.notify_manager_var = tk.BooleanVar(value=self._to_bool(self.state.get("notify_manager", True)))
        self.live_sync_interval_var = tk.StringVar(value=str(self.state.get("live_sync_interval", "20")))
        self.sound_alert_var = tk.BooleanVar(value=self._to_bool(self.state.get("sound_alert", True)))
        self.ai_profile_var = tk.StringVar(value=str(self.state.get("ai_profile", "balanced")))
        self.non_disruptive_mode_var = tk.BooleanVar(value=self._to_bool(self.state.get("non_disruptive_mode", True)))
        self.enforcement_threshold_var = tk.IntVar(
            value=self._safe_int(self.state.get("enforcement_threshold", 84), 84)
        )
        self.block_during_business_hours_var = tk.BooleanVar(
            value=self._to_bool(self.state.get("block_during_business_hours", False))
        )
        self.business_hours_start_var = tk.StringVar(value=str(self.state.get("business_hours_start", "08:00")))
        self.business_hours_end_var = tk.StringVar(value=str(self.state.get("business_hours_end", "20:00")))
        self.trusted_processes_var = tk.StringVar(value=str(self.state.get("trusted_processes", "")))
        self.trusted_domains_var = tk.StringVar(value=str(self.state.get("trusted_domains", "")))
        self.auto_start_on_launch_var = tk.BooleanVar(value=self._to_bool(self.state.get("auto_start_on_launch", False)))
        self.deep_scan_on_start_var = tk.BooleanVar(value=self._to_bool(self.state.get("deep_scan_on_start", True)))
        self.email_risk_alert_var = tk.BooleanVar(value=self._to_bool(self.state.get("email_risk_alert", True)))
        self.web_control_enforce_var = tk.BooleanVar(value=self._to_bool(self.state.get("web_control_enforce", False)))
        self.download_shield_var = tk.BooleanVar(value=self._to_bool(self.state.get("download_shield_enabled", True)))
        self.download_shield_quarantine_var = tk.BooleanVar(value=self._to_bool(self.state.get("download_shield_quarantine", True)))
        self.exploit_guard_var = tk.BooleanVar(value=self._to_bool(self.state.get("exploit_guard_enabled", True)))
        self.exploit_guard_auto_kill_var = tk.BooleanVar(value=self._to_bool(self.state.get("exploit_guard_auto_kill", True)))
        self.beacon_guard_var = tk.BooleanVar(value=self._to_bool(self.state.get("beacon_guard_enabled", True)))
        self.beacon_guard_block_var = tk.BooleanVar(value=self._to_bool(self.state.get("beacon_guard_block", False)))

        self._set_identity()
        self._configure_styles()
        self._build()
        self._load_agent_config_to_ui()
        self._set_admin_unlocked(False)
        self.alert_mode_var.set(
            f"Alert mode: {self.policy_mode_var.get().strip()}/{self.ai_profile_var.get().strip()}"
        )
        self._append_feed("Etherius started in unified mode.")
        if self.auto_start_on_launch_var.get() and self.employee_token_var.get().strip() and self.employee_endpoint_id_var.get().strip():
            self.root.after(1200, self.start_protection)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        try:
            if platform.system() == "Windows":
                self.root.state("zoomed")
        except Exception:
            pass

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
        style.configure("TNotebook", background="#060814")
        style.configure("TNotebook.Tab", background="#0e1428", foreground="#cedbff", padding=(12, 8))
        style.map("TNotebook.Tab", background=[("selected", "#7b61ff"), ("active", "#9277ff")], foreground=[("selected", "#f3f5ff")])
        style.configure(
            "Primary.TButton",
            padding=(12, 8),
            font=("Segoe UI", 10, "bold"),
            foreground="#f6f8ff",
            background="#7b61ff",
            borderwidth=0,
        )
        style.map("Primary.TButton", background=[("active", "#8f75ff"), ("pressed", "#5f46d9")])
        style.configure(
            "Secondary.TButton",
            padding=(10, 7),
            font=("Segoe UI", 10),
            foreground="#cfd9ff",
            background="#182650",
            borderwidth=0,
        )
        style.map("Secondary.TButton", background=[("active", "#233768"), ("pressed", "#132245")])
        style.configure("Header.TLabel", font=("Segoe UI", 18, "bold"), foreground="#edf2ff", background="#060814")
        style.configure("Muted.TLabel", font=("Segoe UI", 10), foreground="#9fb0d8", background="#060814")

    def _build(self):
        shell = tk.Frame(self.root, bg="#060814")
        shell.pack(fill="both", expand=True, padx=18, pady=14)

        top = tk.Frame(shell, bg="#060814")
        top.pack(fill="x", pady=(0, 10))
        self.header_logo_image = None
        try:
            for candidate in [ASSETS / "etherius-wordmark.png", ASSETS / "etherius-suite.png"]:
                if candidate.exists():
                    self.header_logo_image = tk.PhotoImage(file=str(candidate))
                    if candidate.name == "etherius-suite.png":
                        # Keep icon compact in header.
                        self.header_logo_image = self.header_logo_image.subsample(8, 8)
                    else:
                        self.header_logo_image = self.header_logo_image.subsample(4, 4)
                    tk.Label(top, image=self.header_logo_image, bg="#060814").pack(anchor="w", pady=(0, 4))
                    break
        except Exception:
            pass
        ttk.Label(top, text="Etherius Unified Security Console", style="Header.TLabel").pack(anchor="w")
        ttk.Label(
            top,
            text="Unified premium console for manager activation, employee protection, and AI-driven response operations.",
            style="Muted.TLabel",
        ).pack(anchor="w", pady=(4, 0))

        ribbon = tk.Frame(shell, bg="#060814")
        ribbon.pack(fill="x", pady=(2, 10))
        self._build_status_chip(ribbon, "Posture", self.posture_score_var, "#8be8c0").pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._build_status_chip(ribbon, "Endpoint", self.endpoint_health_var, "#cedbff").pack(side="left", fill="x", expand=True, padx=6)
        self._build_status_chip(ribbon, "Cloud Sync", self.live_sync_state_var, "#9fb0d8").pack(side="left", fill="x", expand=True, padx=6)
        self._build_status_chip(ribbon, "Alert Profile", self.alert_mode_var, "#ffb763").pack(side="left", fill="x", expand=True, padx=(6, 0))

        mode_row = tk.Frame(shell, bg="#060814")
        mode_row.pack(fill="x", pady=(0, 8))
        ttk.Button(mode_row, text="Employee View", style="Primary.TButton", command=self._show_employee_section).pack(side="left")
        ttk.Button(mode_row, text="Manager View", style="Secondary.TButton", command=self._request_manager_section).pack(side="left", padx=8)
        tk.Label(
            mode_row,
            text="Employee mode is default. Manager controls unlock only after subscription activation and manager sign-in.",
            bg="#060814",
            fg="#9fb0d8",
            anchor="w",
        ).pack(side="left", padx=10)

        self.notebook = ttk.Notebook(shell)
        self.notebook.pack(fill="both", expand=True)

        self.admin_tab = tk.Frame(self.notebook, bg="#0e1428")
        self.employee_tab = tk.Frame(self.notebook, bg="#0e1428")
        self.ops_tab = tk.Frame(self.notebook, bg="#0e1428")
        self.notebook.add(self.admin_tab, text="Manager Dashboard")
        self.notebook.add(self.employee_tab, text="Employee Protection")
        self.notebook.add(self.ops_tab, text="Security Settings")

        self._build_admin_tab(self.admin_tab)
        self._build_employee_tab(self.employee_tab)
        self._build_ops_tab(self.ops_tab)

        quick_nav = tk.Frame(shell, bg="#060814")
        quick_nav.pack(fill="x", pady=(0, 8))
        ttk.Button(quick_nav, text="Employee Protection", style="Secondary.TButton", command=self._show_employee_section).pack(side="left")
        ttk.Button(quick_nav, text="Manager Dashboard", style="Secondary.TButton", command=self._request_manager_section).pack(side="left", padx=8)
        ttk.Button(quick_nav, text="Security Settings", style="Secondary.TButton", command=self._show_settings_section).pack(side="left")
        ttk.Button(quick_nav, text="Quick Refresh", style="Primary.TButton", command=self._quick_refresh).pack(side="right")
        self._show_employee_section()

    def _request_manager_section(self):
        decision = messagebox.askyesno(
            "Manager Section",
            "Manager section includes customer dashboard and employee license management.\n\nProceed to manager sign-in view?",
        )
        if decision:
            self._show_manager_section()

    def _show_employee_section(self):
        if not self.notebook or not self.admin_tab_visible:
            if self.notebook and self.employee_tab:
                self.notebook.select(self.employee_tab)
            return
        try:
            self.notebook.hide(self.admin_tab)
            self.admin_tab_visible = False
        except Exception:
            pass
        if self.notebook and self.employee_tab:
            self.notebook.select(self.employee_tab)

    def _show_manager_section(self):
        if not self.notebook:
            return
        if not self.admin_tab_visible:
            try:
                self.notebook.insert(0, self.admin_tab, text="Manager Dashboard")
            except Exception:
                self.notebook.add(self.admin_tab, text="Manager Dashboard")
            self.admin_tab_visible = True
        self.notebook.select(self.admin_tab)

    def _show_settings_section(self):
        if self.notebook and self.ops_tab:
            self.notebook.select(self.ops_tab)

    def _quick_refresh(self):
        if self.access_token:
            self.refresh_admin_dashboard(show_errors=False)
            self._append_feed("Quick refresh completed.")
            return
        self._append_feed("Quick refresh skipped: manager not signed in.")

    def _build_status_chip(self, parent, title, variable, color):
        card = tk.Frame(parent, bg="#0e1428", bd=1, relief="groove")
        tk.Label(card, text=title, bg="#0e1428", fg="#9fb0d8", anchor="w").pack(fill="x", padx=10, pady=(6, 0))
        tk.Label(card, textvariable=variable, bg="#0e1428", fg=color, anchor="w", font=("Segoe UI", 10, "bold")).pack(
            fill="x", padx=10, pady=(2, 8)
        )
        return card

    def _build_admin_tab(self, parent):
        wrap = tk.Frame(parent, bg="#0e1428")
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        conn = tk.LabelFrame(wrap, text="Connection", bg="#141f3d", fg="#edf2ff", bd=1, relief="groove")
        conn.pack(fill="x", pady=(0, 10))
        self._labeled_entry(conn, "API URL", self.backend_url_var, width=76).pack(fill="x", padx=10, pady=8)

        auth_row = tk.Frame(wrap, bg="#0e1428")
        auth_row.pack(fill="x", pady=(0, 10))

        activation_box = tk.LabelFrame(
            auth_row,
            text="New Customer Activation (requires subscription license key)",
            bg="#141f3d",
            fg="#edf2ff",
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
            bg="#141f3d",
            fg="#edf2ff",
            bd=1,
            relief="groove",
        )
        signin_box.pack(side="left", fill="both", expand=True, padx=(6, 0))

        self._labeled_entry(signin_box, "Admin Email", self.admin_email_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(signin_box, "Admin Password", self.admin_password_var, show="*").pack(fill="x", padx=10, pady=(8, 0))
        btn_row = tk.Frame(signin_box, bg="#141f3d")
        btn_row.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_row, text="Sign In", style="Primary.TButton", command=self.sign_in_admin).pack(side="left")
        ttk.Button(btn_row, text="Sign Out", style="Secondary.TButton", command=self.sign_out_admin).pack(side="left", padx=8)
        ttk.Button(btn_row, text="Refresh Dashboard", style="Secondary.TButton", command=self.refresh_admin_dashboard).pack(side="left")

        tk.Label(signin_box, textvariable=self.admin_session_var, bg="#141f3d", fg="#8be8c0", anchor="w").pack(fill="x", padx=10, pady=(2, 10))

        dashboard = tk.LabelFrame(wrap, text="In-App Customer Dashboard", bg="#141f3d", fg="#edf2ff", bd=1, relief="groove")
        dashboard.pack(fill="both", expand=True)
        self.admin_locked_overlay = tk.Label(
            dashboard,
            text="Locked. Activate company with subscription key or sign in as admin customer.",
            bg="#1c2b50",
            fg="#ffc783",
            font=("Segoe UI", 10, "bold"),
            padx=10,
            pady=6,
        )
        self.admin_locked_overlay.pack(fill="x", padx=10, pady=(8, 6))

        summary = tk.Frame(dashboard, bg="#141f3d")
        summary.pack(fill="x", padx=10, pady=(0, 6))
        tk.Label(summary, textvariable=self.stats_text_var, bg="#141f3d", fg="#dfe8ff", justify="left", anchor="w").pack(fill="x")
        tk.Label(summary, textvariable=self.company_code_var, bg="#141f3d", fg="#37e79f", anchor="w").pack(fill="x", pady=(2, 0))
        tk.Label(summary, textvariable=self.subscription_status_var, bg="#141f3d", fg="#ffb763", anchor="w").pack(fill="x")
        tk.Label(summary, textvariable=self.subscription_seats_var, bg="#141f3d", fg="#37e79f", anchor="w").pack(fill="x")
        tk.Label(summary, textvariable=self.subscription_capacity_var, bg="#141f3d", fg="#37e79f", anchor="w").pack(fill="x")

        grid = tk.Frame(dashboard, bg="#141f3d")
        grid.pack(fill="both", expand=True, padx=10, pady=(2, 10))

        endpoints_box = tk.LabelFrame(grid, text="Employees / Endpoints", bg="#141f3d", fg="#edf2ff")
        endpoints_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        self.endpoints_list = tk.Listbox(endpoints_box, height=12, bg="#090f1f", fg="#dfe8ff")
        self.endpoints_list.pack(fill="both", expand=True, padx=8, pady=8)

        alerts_box = tk.LabelFrame(grid, text="Open Alerts", bg="#141f3d", fg="#edf2ff")
        alerts_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))
        self.alerts_list = tk.Listbox(alerts_box, height=12, bg="#090f1f", fg="#ffc783")
        self.alerts_list.pack(fill="both", expand=True, padx=8, pady=8)

        keys_box = tk.LabelFrame(grid, text="Employee Activation Keys", bg="#141f3d", fg="#edf2ff")
        keys_box.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        key_form = tk.Frame(keys_box, bg="#141f3d")
        key_form.pack(fill="x", padx=8, pady=8)
        self._labeled_entry(key_form, "Label", self.employee_key_label_var, width=26).grid(row=0, column=0, padx=(0, 8))
        self._labeled_entry(key_form, "Max Activations", self.employee_key_max_var, width=14).grid(row=0, column=1, padx=(0, 8))
        self._labeled_entry(key_form, "Valid Days", self.employee_key_days_var, width=14).grid(row=0, column=2, padx=(0, 8))
        ttk.Button(key_form, text="Generate Employee Key", style="Primary.TButton", command=self.create_employee_key).grid(row=0, column=3)

        self.employee_keys_list = tk.Listbox(keys_box, height=8, bg="#090f1f", fg="#dfe8ff")
        self.employee_keys_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        grid.grid_columnconfigure(0, weight=1)
        grid.grid_columnconfigure(1, weight=1)
        grid.grid_rowconfigure(0, weight=1)
        grid.grid_rowconfigure(1, weight=1)

        controls = tk.LabelFrame(wrap, text="Manager Control Center", bg="#141f3d", fg="#edf2ff", bd=1, relief="groove")
        controls.pack(fill="both", expand=True, pady=(10, 0))
        self._build_manager_control_center(controls)

    def _build_manager_control_center(self, parent):
        tabs = ttk.Notebook(parent)
        tabs.pack(fill="both", expand=True, padx=8, pady=8)

        response_tab = tk.Frame(tabs, bg="#0e1428")
        policy_tab = tk.Frame(tabs, bg="#0e1428")
        intel_tab = tk.Frame(tabs, bg="#0e1428")
        report_tab = tk.Frame(tabs, bg="#0e1428")
        tabs.add(response_tab, text="Remote Response")
        tabs.add(policy_tab, text="USB / App / Web")
        tabs.add(intel_tab, text="Insider / Vulnerability")
        tabs.add(report_tab, text="Compliance Reports")

        # Response tab
        top = tk.Frame(response_tab, bg="#0e1428")
        top.pack(fill="x", padx=10, pady=(10, 6))
        tk.Label(top, text="Endpoint", bg="#0e1428", fg="#9fb0d8").pack(side="left")
        self.endpoint_selector = ttk.Combobox(top, textvariable=self.endpoint_selector_var, state="readonly", width=38)
        self.endpoint_selector.pack(side="left", padx=8)
        ttk.Button(top, text="Lock Screen", style="Secondary.TButton", command=self.lock_selected_endpoint).pack(side="left")
        tk.Entry(top, textvariable=self.remote_message_var, width=40, bg="#0a1124", fg="#edf2ff", insertbackground="#edf2ff").pack(side="left", padx=8)
        ttk.Button(top, text="Send Message", style="Primary.TButton", command=self.send_remote_message).pack(side="left")

        history_box = tk.LabelFrame(response_tab, text="Command History", bg="#141f3d", fg="#cedbff")
        history_box.pack(fill="both", expand=True, padx=10, pady=(4, 10))
        self.command_history_list = tk.Listbox(history_box, bg="#090f1f", fg="#dfe8ff")
        self.command_history_list.pack(fill="both", expand=True, padx=8, pady=8)

        # Policy tab
        policy_top = tk.Frame(policy_tab, bg="#0e1428")
        policy_top.pack(fill="x", padx=10, pady=(10, 8))
        tk.Label(policy_top, text="USB Policy", bg="#0e1428", fg="#9fb0d8").pack(side="left")
        ttk.Combobox(policy_top, textvariable=self.usb_policy_var, values=["allow_all", "block_all", "whitelist"], state="readonly", width=16).pack(
            side="left", padx=8
        )
        ttk.Button(policy_top, text="Apply USB Policy", style="Primary.TButton", command=self.apply_usb_policy).pack(side="left")
        ttk.Button(policy_top, text="Refresh Controls", style="Secondary.TButton", command=self.refresh_manager_controls).pack(side="left", padx=8)

        policy_grid = tk.Frame(policy_tab, bg="#0e1428")
        policy_grid.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        usb_box = tk.LabelFrame(policy_grid, text="USB Devices", bg="#141f3d", fg="#cedbff")
        usb_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6), pady=(0, 6))
        usb_entry = tk.Frame(usb_box, bg="#141f3d")
        usb_entry.pack(fill="x", padx=8, pady=8)
        tk.Entry(usb_entry, textvariable=self.usb_device_id_var, width=28, bg="#0a1124", fg="#edf2ff", insertbackground="#edf2ff").pack(side="left")
        tk.Entry(usb_entry, textvariable=self.usb_device_name_var, width=20, bg="#0a1124", fg="#edf2ff", insertbackground="#edf2ff").pack(side="left", padx=6)
        ttk.Button(usb_entry, text="Whitelist", style="Secondary.TButton", command=self.whitelist_usb_device).pack(side="left")
        self.usb_devices_list = tk.Listbox(usb_box, bg="#090f1f", fg="#dfe8ff", height=8)
        self.usb_devices_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        app_box = tk.LabelFrame(policy_grid, text="Application Blacklist", bg="#141f3d", fg="#cedbff")
        app_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0), pady=(0, 6))
        app_entry = tk.Frame(app_box, bg="#141f3d")
        app_entry.pack(fill="x", padx=8, pady=8)
        tk.Entry(app_entry, textvariable=self.app_name_var, width=24, bg="#0a1124", fg="#edf2ff", insertbackground="#edf2ff").pack(side="left")
        ttk.Combobox(app_entry, textvariable=self.app_action_var, values=["kill", "alert"], state="readonly", width=10).pack(side="left", padx=6)
        ttk.Button(app_entry, text="Add", style="Secondary.TButton", command=self.add_app_blacklist).pack(side="left")
        self.app_blacklist_list = tk.Listbox(app_box, bg="#090f1f", fg="#dfe8ff", height=8)
        self.app_blacklist_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        domain_box = tk.LabelFrame(policy_grid, text="Blocked Domains", bg="#141f3d", fg="#cedbff")
        domain_box.grid(row=1, column=0, columnspan=2, sticky="nsew", pady=(6, 0))
        domain_entry = tk.Frame(domain_box, bg="#141f3d")
        domain_entry.pack(fill="x", padx=8, pady=8)
        tk.Entry(domain_entry, textvariable=self.domain_var, width=30, bg="#0a1124", fg="#edf2ff", insertbackground="#edf2ff").pack(side="left")
        ttk.Combobox(domain_entry, textvariable=self.domain_category_var, values=["custom", "adult", "gambling", "social"], state="readonly", width=12).pack(side="left", padx=6)
        ttk.Button(domain_entry, text="Block Domain", style="Secondary.TButton", command=self.add_blocked_domain).pack(side="left")
        self.domain_list = tk.Listbox(domain_box, bg="#090f1f", fg="#dfe8ff", height=7)
        self.domain_list.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        policy_grid.grid_columnconfigure(0, weight=1)
        policy_grid.grid_columnconfigure(1, weight=1)
        policy_grid.grid_rowconfigure(0, weight=1)
        policy_grid.grid_rowconfigure(1, weight=1)

        # Intelligence tab
        intel_grid = tk.Frame(intel_tab, bg="#0e1428")
        intel_grid.pack(fill="both", expand=True, padx=10, pady=10)
        insider_box = tk.LabelFrame(intel_grid, text="Insider Threat Scores", bg="#141f3d", fg="#cedbff")
        insider_box.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        self.insider_list = tk.Listbox(insider_box, bg="#090f1f", fg="#dfe8ff")
        self.insider_list.pack(fill="both", expand=True, padx=8, pady=8)
        vuln_box = tk.LabelFrame(intel_grid, text="Vulnerability Intelligence", bg="#141f3d", fg="#cedbff")
        vuln_box.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        self.vuln_list = tk.Listbox(vuln_box, bg="#090f1f", fg="#dfe8ff")
        self.vuln_list.pack(fill="both", expand=True, padx=8, pady=8)
        ttk.Button(intel_tab, text="Recalculate Insider Scores", style="Secondary.TButton", command=self.recalculate_insider_scores).pack(
            anchor="e", padx=10, pady=(0, 10)
        )
        intel_grid.grid_columnconfigure(0, weight=1)
        intel_grid.grid_columnconfigure(1, weight=1)
        intel_grid.grid_rowconfigure(0, weight=1)

        # Reports tab
        report_top = tk.Frame(report_tab, bg="#0e1428")
        report_top.pack(fill="x", padx=10, pady=(10, 6))
        tk.Label(report_top, text="Days", bg="#0e1428", fg="#9fb0d8").pack(side="left")
        tk.Entry(report_top, textvariable=self.report_days_var, width=8, bg="#0a1124", fg="#edf2ff", insertbackground="#edf2ff").pack(side="left", padx=6)
        ttk.Button(report_top, text="Refresh Report", style="Primary.TButton", command=self.refresh_report_summary).pack(side="left")
        ttk.Button(report_top, text="Export PDF", style="Secondary.TButton", command=self.export_report_pdf).pack(side="left", padx=8)
        tk.Label(report_top, textvariable=self.compliance_score_var, bg="#0e1428", fg="#8be8c0").pack(side="left", padx=10)
        self.report_summary_text = tk.Text(report_tab, bg="#090f1f", fg="#dfe8ff", relief="flat", height=16)
        self.report_summary_text.pack(fill="both", expand=True, padx=10, pady=(0, 10))
    def _build_employee_tab(self, parent):
        wrap = tk.Frame(parent, bg="#0e1428")
        wrap.pack(fill="both", expand=True, padx=14, pady=14)

        setup = tk.LabelFrame(wrap, text="Employee Activation (same software)", bg="#141f3d", fg="#edf2ff", bd=1, relief="groove")
        setup.pack(fill="x", pady=(0, 10))
        self._labeled_entry(setup, "API URL", self.backend_url_var, width=76).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(setup, "Company Enrollment Code", self.employee_company_code_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(setup, "Employee Activation Key", self.employee_key_var).pack(fill="x", padx=10, pady=(8, 0))
        self._labeled_entry(setup, "Activation Code", self.employee_activation_var).pack(fill="x", padx=10, pady=(8, 0))

        btn_row = tk.Frame(setup, bg="#141f3d")
        btn_row.pack(fill="x", padx=10, pady=10)
        ttk.Button(btn_row, text="Enroll Employee Device", style="Primary.TButton", command=self.enroll_employee_device).pack(side="left")
        ttk.Button(btn_row, text="Apply Activation Code", style="Secondary.TButton", command=self.apply_activation_code).pack(side="left", padx=8)
        ttk.Button(btn_row, text="Start Protection", style="Primary.TButton", command=self.start_protection).pack(side="left", padx=8)
        ttk.Button(btn_row, text="Stop Protection", style="Secondary.TButton", command=self.stop_protection).pack(side="left")

        scan_row = tk.Frame(setup, bg="#141f3d")
        scan_row.pack(fill="x", padx=10, pady=(0, 8))
        ttk.Button(scan_row, text="Quick AI Threat Scan", style="Secondary.TButton", command=self.run_quick_scan).pack(side="left")
        ttk.Button(scan_row, text="Deep Corporate Risk Scan", style="Secondary.TButton", command=self.run_deep_scan).pack(side="left", padx=8)
        tk.Label(scan_row, textvariable=self.scan_summary_var, bg="#141f3d", fg="#ffb763", anchor="w").pack(side="left", padx=10)

        modules = tk.Frame(setup, bg="#141f3d")
        modules.pack(fill="x", padx=10, pady=(0, 8))
        module_items = [
            ("Behavior AI", "#8be8c0"),
            ("Network Guard", "#cedbff"),
            ("File Monitor", "#9fb0d8"),
            ("Threat Response", "#ffb763"),
            ("Download Shield", "#8be8c0"),
            ("Exploit Guard", "#ffc783"),
            ("Beacon Guard", "#ffb763"),
        ]
        for idx, (name, color) in enumerate(module_items):
            cell = tk.Frame(modules, bg="#0a1124", bd=1, relief="groove")
            row = idx // 4
            col = idx % 4
            cell.grid(row=row, column=col, sticky="nsew", padx=(0 if col == 0 else 6, 0), pady=(0 if row == 0 else 6, 0))
            tk.Label(cell, text=name, bg="#0a1124", fg="#9fb0d8", font=("Segoe UI", 9)).pack(anchor="w", padx=8, pady=(6, 0))
            tk.Label(cell, text="Active", bg="#0a1124", fg=color, font=("Segoe UI", 10, "bold")).pack(anchor="w", padx=8, pady=(2, 7))
            modules.grid_columnconfigure(col, weight=1)

        tk.Label(setup, textvariable=self.employee_runtime_var, bg="#141f3d", fg="#8be8c0", anchor="w").pack(fill="x", padx=10)
        tk.Label(setup, textvariable=self.employee_heartbeat_var, bg="#141f3d", fg="#9fb0d8", anchor="w").pack(fill="x", padx=10)
        tk.Label(setup, textvariable=self.employee_events_var, bg="#141f3d", fg="#9fb0d8", anchor="w").pack(fill="x", padx=10, pady=(0, 8))

        details = tk.Frame(wrap, bg="#0e1428")
        details.pack(fill="both", expand=True)

        left = tk.LabelFrame(details, text="Device Identity", bg="#141f3d", fg="#edf2ff")
        left.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right = tk.LabelFrame(details, text="Protection Activity Feed", bg="#141f3d", fg="#edf2ff")
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
            tk.Label(left, text=line, bg="#141f3d", fg="#dfe8ff", anchor="w").pack(fill="x", padx=10, pady=(8, 0))

        self.activity_feed = tk.Text(right, bg="#090f1f", fg="#dfe8ff", relief="flat")
        self.activity_feed.pack(fill="both", expand=True, padx=8, pady=8)

        self.scan_results = tk.Text(left, height=10, bg="#090f1f", fg="#37e79f", relief="flat")
        self.scan_results.pack(fill="both", expand=True, padx=10, pady=(10, 10))

    def _build_ops_tab(self, parent):
        wrap = tk.Frame(parent, bg="#0e1428")
        wrap.pack(fill="both", expand=True, padx=14, pady=14)
        left = tk.LabelFrame(wrap, text="AI Security Controls", bg="#141f3d", fg="#edf2ff")
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.LabelFrame(wrap, text="Platform Operations", bg="#141f3d", fg="#edf2ff")
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        mode_row = tk.Frame(left, bg="#141f3d")
        mode_row.pack(fill="x", padx=12, pady=(12, 6))
        tk.Label(mode_row, text="Protection Policy", bg="#141f3d", fg="#a5b4d8").pack(anchor="w")
        ttk.Combobox(mode_row, textvariable=self.policy_mode_var, values=["advisory", "balanced", "strict"], state="readonly").pack(
            fill="x", pady=(4, 0)
        )

        profile_row = tk.Frame(left, bg="#141f3d")
        profile_row.pack(fill="x", padx=12, pady=(6, 6))
        tk.Label(profile_row, text="AI Decision Profile", bg="#141f3d", fg="#a5b4d8").pack(anchor="w")
        ttk.Combobox(profile_row, textvariable=self.ai_profile_var, values=["conservative", "balanced", "aggressive"], state="readonly").pack(
            fill="x", pady=(4, 0)
        )

        sensitivity_row = tk.Frame(left, bg="#141f3d")
        sensitivity_row.pack(fill="x", padx=12, pady=(6, 6))
        tk.Label(sensitivity_row, text="AI Sensitivity (0-100)", bg="#141f3d", fg="#a5b4d8").pack(anchor="w")
        tk.Scale(
            sensitivity_row,
            from_=0,
            to=100,
            orient="horizontal",
            variable=self.ai_sensitivity_var,
            bg="#141f3d",
            fg="#edf2ff",
            troughcolor="#294072",
            highlightthickness=0,
        ).pack(fill="x")

        threshold_row = tk.Frame(left, bg="#141f3d")
        threshold_row.pack(fill="x", padx=12, pady=(6, 6))
        tk.Label(threshold_row, text="Auto-Enforcement Threshold (safe default 84)", bg="#141f3d", fg="#a5b4d8").pack(anchor="w")
        tk.Scale(
            threshold_row,
            from_=50,
            to=95,
            orient="horizontal",
            variable=self.enforcement_threshold_var,
            bg="#141f3d",
            fg="#edf2ff",
            troughcolor="#294072",
            highlightthickness=0,
        ).pack(fill="x")

        auto_row = tk.Frame(left, bg="#141f3d")
        auto_row.pack(fill="x", padx=12, pady=(6, 6))
        self._labeled_entry(auto_row, "Auto Scan Interval (minutes)", self.auto_scan_interval_var, width=20).pack(fill="x")

        sync_row = tk.Frame(left, bg="#141f3d")
        sync_row.pack(fill="x", padx=12, pady=(6, 6))
        self._labeled_entry(sync_row, "Live Manager Sync (seconds)", self.live_sync_interval_var, width=20).pack(fill="x")

        notify_row = tk.Frame(left, bg="#141f3d")
        notify_row.pack(fill="x", padx=12, pady=(6, 6))
        tk.Checkbutton(
            notify_row,
            text="Non-disruptive mode (detect first, enforce only at high confidence)",
            variable=self.non_disruptive_mode_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Allow enforcement during business hours",
            variable=self.block_during_business_hours_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Send scan intelligence to manager dashboard",
            variable=self.notify_manager_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Sound alert for critical events in software",
            variable=self.sound_alert_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Enable email-risk escalation tagging",
            variable=self.email_risk_alert_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Enforce web policy alerts in employee runtime",
            variable=self.web_control_enforce_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        self._labeled_entry(notify_row, "Business hours start (HH:MM)", self.business_hours_start_var, width=16).pack(
            fill="x", pady=(6, 0)
        )
        self._labeled_entry(notify_row, "Business hours end (HH:MM)", self.business_hours_end_var, width=16).pack(
            fill="x", pady=(6, 0)
        )
        self._labeled_entry(
            notify_row,
            "Trusted processes (comma-separated executable names)",
            self.trusted_processes_var,
            width=64,
        ).pack(fill="x", pady=(6, 0))
        self._labeled_entry(
            notify_row,
            "Trusted domains (comma-separated domains)",
            self.trusted_domains_var,
            width=64,
        ).pack(fill="x", pady=(6, 0))
        tk.Checkbutton(
            notify_row,
            text="Auto-start protection on launch (if activation exists)",
            variable=self.auto_start_on_launch_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Run deep scan automatically at protection start",
            variable=self.deep_scan_on_start_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Enable Download Shield (suspicious file detection)",
            variable=self.download_shield_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Auto-quarantine suspicious downloads in balanced/strict mode",
            variable=self.download_shield_quarantine_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Enable Exploit Guard (office/browser exploit-chain detection)",
            variable=self.exploit_guard_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Auto-kill exploit-chain process in balanced/strict mode",
            variable=self.exploit_guard_auto_kill_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Enable Beacon Guard (persistent C2/exfil traffic detection)",
            variable=self.beacon_guard_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")
        tk.Checkbutton(
            notify_row,
            text="Strict mode: apply local outbound firewall block for beacon IPs",
            variable=self.beacon_guard_block_var,
            bg="#141f3d",
            fg="#dfe8ff",
            activebackground="#141f3d",
            activeforeground="#dfe8ff",
            selectcolor="#20305a",
        ).pack(anchor="w")

        actions = tk.Frame(left, bg="#141f3d")
        actions.pack(fill="x", padx=12, pady=(8, 12))
        ttk.Button(actions, text="Save Security Settings", style="Primary.TButton", command=self.save_security_settings).pack(side="left")
        ttk.Button(actions, text="Refresh All Manager Controls", style="Secondary.TButton", command=self.refresh_admin_dashboard).pack(side="left", padx=8)

        info_lines = [
            "Core posture:",
            "- One setup, one software, dual-role secure architecture.",
            "- Manager dashboard hidden in default employee mode.",
            "- Subscription-key activation required for manager onboarding.",
            "- Employee keys are quantity-limited by purchased seat count.",
            "",
            "AI protection capabilities:",
            "- Process and command-line threat heuristics",
            "- Suspicious network C2-like port detection",
            "- Sensitive-path executable/script inspection",
            "- Email lure and phishing-indicator analysis",
            "- USB/App/Web/DLP/Vulnerability policy-integrated telemetry",
            "- Download Shield for suspicious installer/script quarantining",
            "- Exploit Guard for office/browser process-chain attacks",
            "- Beacon Guard for persistent C2/exfiltration traffic patterns",
            "- Local quick/deep risk scanning with decision-aware escalation",
            "- Adaptive non-disruptive enforcement guard with confidence thresholding",
            "- Trusted business app/domain allowlists to avoid workflow interruption",
            "",
            "Safety principle:",
            "- Advisory-first: critical business tools are allowlisted and not auto-blocked by default.",
            "- Strict mode increases detection sensitivity and response recommendations.",
            "- Non-disruptive mode keeps protection strong while reducing accidental workflow stops.",
        ]
        for line in info_lines:
            tk.Label(right, text=line, bg="#141f3d", fg="#dfe8ff", anchor="w", justify="left").pack(fill="x", padx=12, pady=(8, 0))

    def _labeled_entry(self, parent, label, variable, width=34, show=None):
        frame = tk.Frame(parent, bg=parent["bg"])
        tk.Label(frame, text=label, bg=parent["bg"], fg="#9fb0d8", anchor="w").pack(anchor="w")
        tk.Entry(frame, textvariable=variable, width=width, show=show, bg="#0a1124", fg="#edf2ff", insertbackground="#edf2ff").pack(fill="x", pady=(3, 0))
        return frame

    def _safe_int(self, value, default=0):
        try:
            return int(value)
        except Exception:
            return default

    def _valid_hhmm(self, value):
        text = str(value or "").strip()
        try:
            hh, mm = text.split(":")
            hh_i = int(hh)
            mm_i = int(mm)
            return 0 <= hh_i <= 23 and 0 <= mm_i <= 59
        except Exception:
            return False

    def _to_bool(self, value):
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in {"1", "true", "yes", "on"}

    def _csv_string(self, value):
        if isinstance(value, (list, tuple, set)):
            return ", ".join([str(v).strip() for v in value if str(v).strip()])
        return str(value or "")

    def _sync_agent_runtime_config(self):
        trusted_processes = [x.strip() for x in self.trusted_processes_var.get().replace(";", ",").split(",") if x.strip()]
        trusted_domains = [x.strip() for x in self.trusted_domains_var.get().replace(";", ",").split(",") if x.strip()]
        payload = {
            "backend_url": self.backend_url_var.get().strip(),
            "company_code": self.employee_company_code_var.get().strip(),
            "employee_key": self.employee_key_var.get().strip(),
            "activation_code": self.employee_activation_var.get().strip(),
            "endpoint_id": self.employee_endpoint_id_var.get().strip(),
            "agent_token": self.employee_token_var.get().strip(),
            "policy_mode": self.policy_mode_var.get().strip(),
            "ai_profile": self.ai_profile_var.get().strip(),
            "ai_sensitivity": int(self.ai_sensitivity_var.get() or 70),
            "non_disruptive_mode": bool(self.non_disruptive_mode_var.get()),
            "enforcement_threshold": int(self.enforcement_threshold_var.get() or 84),
            "block_during_business_hours": bool(self.block_during_business_hours_var.get()),
            "business_hours_start": self.business_hours_start_var.get().strip() or "08:00",
            "business_hours_end": self.business_hours_end_var.get().strip() or "20:00",
            "trusted_processes": trusted_processes,
            "trusted_domains": trusted_domains,
            "web_control_enforce": bool(self.web_control_enforce_var.get()),
            "download_shield_enabled": bool(self.download_shield_var.get()),
            "download_shield_quarantine": bool(self.download_shield_quarantine_var.get()),
            "exploit_guard_enabled": bool(self.exploit_guard_var.get()),
            "exploit_guard_auto_kill": bool(self.exploit_guard_auto_kill_var.get()),
            "beacon_guard_enabled": bool(self.beacon_guard_var.get()),
            "beacon_guard_block": bool(self.beacon_guard_block_var.get()),
        }
        update_config(payload)
        return payload

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
            detail_msg = response.text
            try:
                body = response.json()
                detail = body.get("detail", body)
                if isinstance(detail, list):
                    parsed = []
                    for item in detail:
                        if isinstance(item, dict):
                            message = str(item.get("msg", "Validation error")).strip()
                            loc = item.get("loc", [])
                            field = str(loc[-1]) if isinstance(loc, (list, tuple)) and loc else ""
                            parsed.append(f"{field}: {message}" if field else message)
                        else:
                            parsed.append(str(item))
                    detail_msg = "; ".join([p for p in parsed if p]) or "Validation failed."
                elif isinstance(detail, dict):
                    detail_msg = ", ".join([f"{k}: {v}" for k, v in detail.items()]) or "Request failed."
                else:
                    detail_msg = str(detail)
            except Exception:
                detail_msg = response.text or f"HTTP {response.status_code}"
            code_hints = {
                400: "Check entered values.",
                401: "Authentication failed. Verify credentials.",
                403: "Access denied or inactive subscription.",
                404: "Requested resource was not found.",
                409: "Duplicate/conflicting data.",
                422: "Some fields are invalid.",
                429: "Too many attempts. Please wait and retry.",
            }
            hint = code_hints.get(response.status_code, "Request failed.")
            lower_detail = str(detail_msg).lower()
            if "password must be at least 12 chars" in lower_detail:
                raise RuntimeError(
                    "Password policy failed: use at least 12 characters with uppercase, lowercase, number, and symbol."
                )
            if "company name already exists" in lower_detail:
                raise RuntimeError("This company name is already registered. Use a different company name.")
            if "invalid or expired subscription key" in lower_detail:
                raise RuntimeError("Subscription key is invalid or expired. Check key value and validity.")
            if "invalid credentials" in lower_detail:
                raise RuntimeError("Email or password is incorrect.")
            if "too many failed logins" in lower_detail:
                raise RuntimeError("Too many failed sign-in attempts. Please wait 15 minutes and retry.")
            raise RuntimeError(f"{detail_msg} ({hint})")
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
            signed_in = self.sign_in_admin(show_success=False)
            self._append_feed("Company activated with subscription license key.")
            if signed_in:
                self._show_manager_section()
                messagebox.showinfo(
                    "Activated",
                    "Company activation successful.\n\nManager dashboard is now unlocked in this same software window.",
                )
            else:
                messagebox.showwarning(
                    "Activated",
                    "Company activation was successful, but sign-in did not complete.\nPlease sign in with admin email and password.",
                )
        except Exception as error:
            messagebox.showerror("Activation failed", str(error))

    def sign_in_admin(self, show_success=True):
        payload = {
            "email": self.admin_email_var.get().strip(),
            "password": self.admin_password_var.get().strip(),
        }
        if not payload["email"] or not payload["password"]:
            messagebox.showerror("Missing credentials", "Enter admin email and password.")
            return False
        try:
            data = self._request("POST", "/api/auth/login", payload=payload, auth=False)
            role = str(data.get("role", "")).lower()
            if role not in {"manager", "admin", "superadmin"}:
                raise RuntimeError("This account cannot access manager dashboard.")
            self._show_manager_section()
            self.access_token = data["access_token"]
            self.admin_role = role
            self.admin_name = data.get("full_name") or payload["email"]
            self.admin_session_var.set(f"Signed in as {self.admin_name} ({self.admin_role})")
            self.live_sync_state_var.set("Cloud sync: authenticated")
            self._set_admin_unlocked(True)
            self.refresh_admin_dashboard()
            self._schedule_admin_live_refresh()
            if show_success:
                messagebox.showinfo(
                    "Signed in",
                    "Admin dashboard is unlocked in this software.\n\n"
                    "Open it in this same Manager Dashboard screen:\n"
                    "- In-App Customer Dashboard\n"
                    "- Manager Control Center\n\n"
                    "If not fully visible, maximize the window.",
                )
            self._append_feed("Admin signed in and dashboard unlocked.")
            return True
        except Exception as error:
            self._set_admin_unlocked(False)
            messagebox.showerror("Sign in failed", str(error))
            return False

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
        self.live_sync_state_var.set("Cloud sync: disconnected")
        self._clear_list(self.endpoints_list)
        self._clear_list(self.alerts_list)
        self._clear_list(self.employee_keys_list)
        self._cancel_admin_live_refresh()
        self._append_feed("Admin signed out.")
        self._show_employee_section()
    def refresh_admin_dashboard(self, show_errors=True, write_feed=True):
        if not self.access_token:
            if show_errors:
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
            if show_errors:
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
        self.live_sync_state_var.set(
            f"Cloud sync: {stats.get('online_endpoints', 0)} endpoints online | {datetime.now().strftime('%H:%M:%S')}"
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

        self.endpoint_lookup = {f"{ep.get('hostname', '-')} ({ep.get('id', '')[:8]})": ep.get("id") for ep in endpoints}
        if self.endpoint_selector:
            self.endpoint_selector["values"] = list(self.endpoint_lookup.keys())
            if not self.endpoint_selector_var.get() and self.endpoint_selector["values"]:
                self.endpoint_selector_var.set(self.endpoint_selector["values"][0])

        self.refresh_manager_controls()
        if write_feed:
            self._append_feed("Admin dashboard data refreshed.")

    def refresh_manager_controls(self):
        if not self.access_token:
            return
        try:
            usb_policy = self._request("GET", "/api/dashboard/usb-policy", auth=True)
            usb_devices = self._request("GET", "/api/dashboard/usb-whitelist", auth=True)
            app_blacklist = self._request("GET", "/api/dashboard/app-blacklist", auth=True)
            blocked_domains = self._request("GET", "/api/dashboard/blocked-domains", auth=True)
            insider_scores = self._request("GET", "/api/dashboard/insider-scores?recalculate=false", auth=True)
            vulnerabilities = self._request("GET", "/api/dashboard/vulnerabilities", auth=True)
            command_history = self._request("GET", "/api/dashboard/command-history?limit=80", auth=True)
        except Exception as error:
            self._append_feed(f"Manager controls refresh failed: {error}")
            return

        self.usb_policy_var.set(usb_policy.get("policy", "allow_all"))

        self._clear_list(self.usb_devices_list)
        for item in usb_devices:
            status = "WHITELISTED" if item.get("is_whitelisted") else "BLOCKED"
            line = f"{item.get('device_id', '-'):<30} | {status:<11} | {item.get('device_name', '-')}"
            self.usb_devices_list.insert("end", line)
        if not usb_devices and self.usb_devices_list:
            self.usb_devices_list.insert("end", "No USB devices captured yet.")

        self._clear_list(self.app_blacklist_list)
        for item in app_blacklist:
            line = f"{item.get('app_name', '-')} | action={item.get('action', 'kill')} | id={item.get('id', '')[:8]}"
            self.app_blacklist_list.insert("end", line)
        if not app_blacklist and self.app_blacklist_list:
            self.app_blacklist_list.insert("end", "No app blacklist entries.")

        self._clear_list(self.domain_list)
        for item in blocked_domains:
            status = "active" if item.get("is_active") else "disabled"
            line = f"{item.get('domain', '-')} | {item.get('category', 'custom')} | {status}"
            self.domain_list.insert("end", line)
        if not blocked_domains and self.domain_list:
            self.domain_list.insert("end", "No blocked domains configured.")

        self._clear_list(self.insider_list)
        for item in insider_scores[:100]:
            line = f"{item.get('hostname', '-'): <28} | score={item.get('score', 0):>3} | trend={item.get('trend', 'stable')}"
            self.insider_list.insert("end", line)
        if not insider_scores and self.insider_list:
            self.insider_list.insert("end", "No insider scores available yet.")

        self._clear_list(self.vuln_list)
        vuln_endpoints = vulnerabilities.get("endpoints", []) if isinstance(vulnerabilities, dict) else []
        for item in vuln_endpoints[:120]:
            line = f"{item.get('endpoint_id', '')[:8]} | vulns={item.get('vuln_count', 0)} | critical={item.get('critical_count', 0)}"
            self.vuln_list.insert("end", line)
        if not vuln_endpoints and self.vuln_list:
            self.vuln_list.insert("end", "No vulnerability inventory uploaded yet.")

        self._clear_list(self.command_history_list)
        for item in command_history[:120]:
            line = f"{item.get('command_type', '-'):<14} | {item.get('status', '-'):<8} | ep={str(item.get('endpoint_id', ''))[:8]}"
            self.command_history_list.insert("end", line)
        if not command_history and self.command_history_list:
            self.command_history_list.insert("end", "No command history yet.")

        self.refresh_report_summary(show_errors=False)

    def _resolve_selected_endpoint_id(self):
        label = self.endpoint_selector_var.get().strip()
        endpoint_id = self.endpoint_lookup.get(label)
        if endpoint_id:
            return endpoint_id
        return ""

    def lock_selected_endpoint(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        endpoint_id = self._resolve_selected_endpoint_id()
        if not endpoint_id:
            messagebox.showerror("Missing endpoint", "Select an endpoint first.")
            return
        try:
            self._request("POST", "/api/response/lock-screen", payload={"endpoint_id": endpoint_id}, auth=True)
            self._append_feed("Lock-screen command queued.")
            self.refresh_manager_controls()
        except Exception as error:
            messagebox.showerror("Command failed", str(error))

    def send_remote_message(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        endpoint_id = self._resolve_selected_endpoint_id()
        message = self.remote_message_var.get().strip()
        if not endpoint_id or not message:
            messagebox.showerror("Missing input", "Select an endpoint and type a message.")
            return
        try:
            self._request(
                "POST",
                "/api/response/remote-message",
                payload={"endpoint_id": endpoint_id, "message": message},
                auth=True,
            )
            self.remote_message_var.set("")
            self._append_feed("Remote message command queued.")
            self.refresh_manager_controls()
        except Exception as error:
            messagebox.showerror("Command failed", str(error))

    def apply_usb_policy(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        try:
            self._request("POST", "/api/dashboard/usb-policy", payload={"policy": self.usb_policy_var.get().strip()}, auth=True)
            self._append_feed(f"USB policy updated to {self.usb_policy_var.get().strip()}.")
            self.refresh_manager_controls()
        except Exception as error:
            messagebox.showerror("USB policy failed", str(error))

    def whitelist_usb_device(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        device_id = self.usb_device_id_var.get().strip()
        if not device_id:
            messagebox.showerror("Missing input", "Enter USB device ID.")
            return
        payload = {
            "device_id": device_id,
            "device_name": self.usb_device_name_var.get().strip(),
            "vendor": "",
            "size": "",
            "is_whitelisted": True,
        }
        try:
            self._request("POST", "/api/dashboard/usb-whitelist", payload=payload, auth=True)
            self._append_feed(f"USB device whitelisted: {device_id}")
            self.usb_device_id_var.set("")
            self.usb_device_name_var.set("")
            self.refresh_manager_controls()
        except Exception as error:
            messagebox.showerror("USB whitelist failed", str(error))

    def add_app_blacklist(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        app_name = self.app_name_var.get().strip().lower()
        if not app_name:
            messagebox.showerror("Missing input", "Enter an app name.")
            return
        payload = {"app_name": app_name, "action": self.app_action_var.get().strip().lower() or "kill"}
        try:
            self._request("POST", "/api/dashboard/app-blacklist", payload=payload, auth=True)
            self._append_feed(f"App blacklist updated: {app_name}")
            self.app_name_var.set("")
            self.refresh_manager_controls()
        except Exception as error:
            messagebox.showerror("App blacklist failed", str(error))

    def add_blocked_domain(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        domain = self.domain_var.get().strip()
        if not domain:
            messagebox.showerror("Missing input", "Enter a domain.")
            return
        payload = {"domain": domain, "category": self.domain_category_var.get().strip(), "is_active": True}
        try:
            self._request("POST", "/api/dashboard/blocked-domains", payload=payload, auth=True)
            self._append_feed(f"Domain blocked: {domain}")
            self.domain_var.set("")
            self.refresh_manager_controls()
        except Exception as error:
            messagebox.showerror("Domain block failed", str(error))

    def recalculate_insider_scores(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        try:
            self._request("GET", "/api/dashboard/insider-scores?recalculate=true", auth=True)
            self._append_feed("Insider threat scores recalculated.")
            self.refresh_manager_controls()
        except Exception as error:
            messagebox.showerror("Recalculation failed", str(error))

    def refresh_report_summary(self, show_errors=True):
        if not self.access_token:
            return
        days = self._safe_int(self.report_days_var.get().strip(), 30)
        days = max(1, min(days, 365))
        self.report_days_var.set(str(days))
        try:
            summary = self._request("GET", f"/api/dashboard/reports/security-summary?days={days}", auth=True)
        except Exception as error:
            if show_errors:
                messagebox.showerror("Report refresh failed", str(error))
            return

        compliance = int(summary.get("compliance_score", 0))
        self.compliance_score_var.set(f"Compliance Score: {compliance}/100")

        if self.report_summary_text:
            self.report_summary_text.delete("1.0", "end")
            lines = [
                f"Window: last {days} day(s)",
                f"Compliance score: {compliance}/100",
                f"Blocked threats: {summary.get('blocked_threats_count', 0)}",
                f"Policy violations: {summary.get('policy_violations', 0)}",
                "",
                "Alerts by severity:",
            ]
            sev = summary.get("alerts_by_severity", {})
            lines.extend(
                [
                    f"- critical: {sev.get('critical', 0)}",
                    f"- high: {sev.get('high', 0)}",
                    f"- medium: {sev.get('medium', 0)}",
                    f"- low/info: {sev.get('low_or_info', 0)}",
                    "",
                    "Top risky endpoints:",
                ]
            )
            for endpoint in summary.get("top_risky_endpoints", [])[:8]:
                lines.append(f"- {endpoint.get('hostname', '-')} : {endpoint.get('risk_score', 0)}")
            lines.append("")
            lines.append("Top threats:")
            for threat in summary.get("top_threats", [])[:8]:
                lines.append(f"- {threat.get('event_type', '-')}: {threat.get('count', 0)}")
            self.report_summary_text.insert("end", "\n".join(lines))

    def export_report_pdf(self):
        if not self.access_token:
            messagebox.showerror("Locked", "Sign in as manager first.")
            return
        days = self._safe_int(self.report_days_var.get().strip(), 30)
        base = self.backend_url_var.get().strip().rstrip("/")
        url = f"{base}/api/dashboard/reports/export-pdf?days={days}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        try:
            response = requests.get(url, headers=headers, timeout=30)
            if response.status_code >= 400:
                raise RuntimeError(response.text)
            target = filedialog.asksaveasfilename(
                title="Save Etherius Security Report",
                defaultextension=".pdf",
                filetypes=[("PDF files", "*.pdf")],
                initialfile=f"etherius-security-summary-{days}d.pdf",
            )
            if not target:
                return
            Path(target).write_bytes(response.content)
            self._append_feed(f"Report PDF exported: {target}")
            messagebox.showinfo("Export complete", "Compliance PDF report exported successfully.")
        except Exception as error:
            messagebox.showerror("Export failed", str(error))

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

        self._sync_agent_runtime_config()
        self.agent.start()
        self.employee_runtime_var.set("Protection active")
        self.endpoint_health_var.set("Endpoint health: protection active")
        self._append_feed("Protection started.")
        if self.deep_scan_on_start_var.get():
            self.root.after(2800, lambda: self._run_local_scan(deep=True))
        self._schedule_auto_scan(initial_delay_seconds=12)

    def stop_protection(self):
        self._cancel_auto_scan()
        self.agent.stop()
        self.employee_runtime_var.set("Protection offline")
        self.endpoint_health_var.set("Endpoint health: protection offline")
        self._append_feed("Protection stopped.")

    def save_security_settings(self):
        interval = self.auto_scan_interval_var.get().strip()
        if not interval.isdigit() or int(interval) <= 0:
            messagebox.showerror("Invalid settings", "Auto scan interval must be a positive number.")
            return
        live_sync = self.live_sync_interval_var.get().strip()
        if not live_sync.isdigit() or int(live_sync) <= 0:
            messagebox.showerror("Invalid settings", "Live manager sync must be a positive number of seconds.")
            return
        if not self._valid_hhmm(self.business_hours_start_var.get().strip()):
            messagebox.showerror("Invalid settings", "Business hours start must be HH:MM (24h format).")
            return
        if not self._valid_hhmm(self.business_hours_end_var.get().strip()):
            messagebox.showerror("Invalid settings", "Business hours end must be HH:MM (24h format).")
            return
        self._save_state()
        self._sync_agent_runtime_config()
        self.alert_mode_var.set(
            f"Alert mode: {self.policy_mode_var.get().strip()}/{self.ai_profile_var.get().strip()}"
        )
        self._append_feed(
            f"Security settings saved: mode={self.policy_mode_var.get()}, profile={self.ai_profile_var.get()}, sensitivity={self.ai_sensitivity_var.get()}, threshold={self.enforcement_threshold_var.get()}, non_disruptive={int(self.non_disruptive_mode_var.get())}, interval={interval}m, shields(download/exploit/beacon)={int(self.download_shield_var.get())}/{int(self.exploit_guard_var.get())}/{int(self.beacon_guard_var.get())}."
        )
        if self.agent.running:
            self._schedule_auto_scan(initial_delay_seconds=10)
        if self.access_token:
            self._schedule_admin_live_refresh()
        messagebox.showinfo("Saved", "Security settings saved successfully.")

    def run_quick_scan(self):
        self._start_scan(deep=False)

    def run_deep_scan(self):
        self._start_scan(deep=True)

    def _start_scan(self, deep=False):
        if self.scan_running:
            self._append_feed("Scan already running. Please wait.")
            return
        self.scan_running = True
        self.scan_summary_var.set("Scan running...")
        policy_mode = str(self.policy_mode_var.get() or "advisory").lower()
        sensitivity = int(self.ai_sensitivity_var.get() or 70)
        ai_profile = str(self.ai_profile_var.get() or "balanced").lower()
        notify_manager = bool(self.notify_manager_var.get())

        def worker():
            try:
                result = self._run_local_scan(
                    deep=deep,
                    policy_mode=policy_mode,
                    sensitivity=sensitivity,
                    ai_profile=ai_profile,
                    notify_manager=notify_manager,
                )
                self.root.after(0, lambda: self._apply_scan_result(result))
            except Exception as error:
                self.root.after(0, lambda: messagebox.showerror("Scan failed", str(error)))
            finally:
                self.root.after(0, self._finish_scan)

        import threading

        threading.Thread(target=worker, daemon=True).start()

    def _finish_scan(self):
        self.scan_running = False

    def _run_local_scan(self, deep=False, policy_mode="advisory", sensitivity=70, ai_profile="balanced", notify_manager=True):
        force_deep = deep or policy_mode == "strict"
        scan_data = run_threat_scan(deep=force_deep)
        summary = scan_data["summary"]
        findings = scan_data["findings"]
        raw_score = int(summary.get("local_scan_risk_score", 0))
        profile_shift = {"conservative": -6, "balanced": 0, "aggressive": 8}.get(ai_profile, 0)
        adjusted_score = max(0, min(100, raw_score + int((sensitivity - 70) * 0.4) + profile_shift))
        adjusted_severity = (
            "critical" if adjusted_score >= 85 else "high" if adjusted_score >= 65 else "medium" if adjusted_score >= 40 else "low"
        )
        recommended_action = (
            "ISOLATE_RECOMMENDED"
            if adjusted_score >= 85
            else "AUTO_BLOCK_RECOMMENDED"
            if adjusted_score >= 65
            else "ALERT_RECOMMENDED"
            if adjusted_score >= 40
            else "MONITOR"
        )
        summary["policy_mode"] = policy_mode
        summary["scan_depth"] = "deep" if force_deep else "quick"
        summary["local_scan_risk_score_raw"] = raw_score
        summary["local_scan_risk_score"] = adjusted_score
        summary["local_scan_severity"] = adjusted_severity
        summary["ai_sensitivity"] = sensitivity
        summary["ai_profile"] = ai_profile
        summary["recommended_action"] = recommended_action
        event_payload = {
            **summary,
            "findings_preview": {
                "process_hits": findings.get("process_hits", [])[:5],
                "network_hits": findings.get("network_hits", [])[:5],
                "filesystem_hits": findings.get("filesystem_hits", [])[:5],
            },
        }
        return {
            "summary": summary,
            "findings": findings,
            "event_payload": event_payload,
            "notify_manager": notify_manager,
        }

    def _apply_scan_result(self, result):
        summary = result["summary"]
        findings = result["findings"]
        event_payload = result["event_payload"]
        notify_manager = result["notify_manager"]
        policy_mode = summary.get("policy_mode", "advisory")
        ai_profile = summary.get("ai_profile", "balanced")
        recommended_action = summary.get("recommended_action", "MONITOR")
        self.scan_summary_var.set(
            f"{summary['scan_depth'].upper()} scan: {summary['local_scan_severity']} ({summary['local_scan_risk_score']}/100), action={recommended_action}"
        )
        self.posture_score_var.set(
            f"Protection posture: {summary['local_scan_severity']} ({summary['local_scan_risk_score']}/100)"
        )
        self._render_scan_results(summary, findings)
        self._append_feed(
            f"{summary['scan_depth'].upper()} scan completed with adjusted risk {summary['local_scan_risk_score']} (policy={policy_mode}, profile={ai_profile})."
        )
        if notify_manager:
            self._send_scan_event(event_payload)
        else:
            self._append_feed("Manager notifications disabled for scan telemetry by policy setting.")
        if policy_mode == "strict" and int(summary.get("local_scan_risk_score", 0)) >= 85:
            self._append_feed("Strict policy alert: isolate endpoint review recommended (manual manager decision).")

    def _schedule_auto_scan(self, initial_delay_seconds=5):
        self._cancel_auto_scan()
        interval_minutes = self._safe_int(self.auto_scan_interval_var.get().strip(), 30)
        if interval_minutes <= 0:
            interval_minutes = 30
        self.auto_scan_job = self.root.after(max(1, int(initial_delay_seconds)) * 1000, self._auto_scan_tick)
        self._append_feed(f"Auto scan scheduler armed ({interval_minutes} minute interval).")

    def _schedule_admin_live_refresh(self):
        self._cancel_admin_live_refresh()
        seconds = self._safe_int(self.live_sync_interval_var.get().strip(), 20)
        if seconds <= 0:
            seconds = 20
        self.admin_live_job = self.root.after(max(5, seconds) * 1000, self._admin_live_tick)

    def _cancel_admin_live_refresh(self):
        if self.admin_live_job:
            try:
                self.root.after_cancel(self.admin_live_job)
            except Exception:
                pass
            self.admin_live_job = None

    def _admin_live_tick(self):
        self.admin_live_job = None
        if not self.access_token:
            return
        self.refresh_admin_dashboard(show_errors=False, write_feed=False)
        self._schedule_admin_live_refresh()

    def _cancel_auto_scan(self):
        if self.auto_scan_job:
            try:
                self.root.after_cancel(self.auto_scan_job)
            except Exception:
                pass
            self.auto_scan_job = None

    def _auto_scan_tick(self):
        self.auto_scan_job = None
        if not self.agent.running:
            return
        if self.scan_running:
            interval_minutes = self._safe_int(self.auto_scan_interval_var.get().strip(), 30)
            if interval_minutes <= 0:
                interval_minutes = 30
            self.auto_scan_job = self.root.after(interval_minutes * 60 * 1000, self._auto_scan_tick)
            return
        deep = self.policy_mode_var.get().strip().lower() == "strict" or random.random() < 0.25
        self._start_scan(deep=deep)
        interval_minutes = self._safe_int(self.auto_scan_interval_var.get().strip(), 30)
        if interval_minutes <= 0:
            interval_minutes = 30
        self.auto_scan_job = self.root.after(interval_minutes * 60 * 1000, self._auto_scan_tick)

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
            f"AI profile: {summary.get('ai_profile', 'balanced')}",
            f"Recommended action: {summary.get('recommended_action', 'MONITOR')}",
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
        if status.get("heartbeat_ok"):
            self.endpoint_health_var.set(
                f"Endpoint health: stable | sent={status.get('events_sent', 0)}"
            )
        else:
            self.endpoint_health_var.set("Endpoint health: reconnecting")

    def _format_agent_event(self, item):
        kind = item.get("kind", "event").upper()
        event_type = item.get("event_type", "unknown")
        decision = item.get("decision")
        detail = item.get("error") or item.get("detail") or item.get("status_code") or ""
        if decision:
            detail = f"{detail} | decision={decision}".strip()
        return f"{kind} | {event_type} {detail}".strip()

    def _append_feed(self, text):
        if not self.activity_feed:
            return
        stamp = datetime.now().strftime("%H:%M:%S")
        self.activity_feed.insert("end", f"[{stamp}] {text}\n")
        self.activity_feed.see("end")
        lowered = str(text).lower()
        if self.sound_alert_var.get() and ("critical" in lowered or "decision=critical" in lowered):
            self._play_alert_tone()

    def _play_alert_tone(self):
        try:
            if platform.system() == "Windows":
                import winsound

                winsound.Beep(950, 120)
            else:
                self.root.bell()
        except Exception:
            pass

    def _set_admin_unlocked(self, unlocked: bool):
        self.admin_locked_overlay.configure(
            text="Dashboard unlocked in software." if unlocked else "Locked. Activate company with subscription key or sign in as admin customer.",
            fg="#37e79f" if unlocked else "#ffc783",
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
        self.policy_mode_var.set(str(cfg.get("policy_mode", self.policy_mode_var.get())))
        self.ai_profile_var.set(str(cfg.get("ai_profile", self.ai_profile_var.get())))
        self.ai_sensitivity_var.set(self._safe_int(cfg.get("ai_sensitivity", self.ai_sensitivity_var.get()), 70))
        self.non_disruptive_mode_var.set(
            self._to_bool(cfg.get("non_disruptive_mode", self.non_disruptive_mode_var.get()))
        )
        self.enforcement_threshold_var.set(
            self._safe_int(cfg.get("enforcement_threshold", self.enforcement_threshold_var.get()), 84)
        )
        self.block_during_business_hours_var.set(
            self._to_bool(cfg.get("block_during_business_hours", self.block_during_business_hours_var.get()))
        )
        self.business_hours_start_var.set(str(cfg.get("business_hours_start", self.business_hours_start_var.get())))
        self.business_hours_end_var.set(str(cfg.get("business_hours_end", self.business_hours_end_var.get())))
        self.trusted_processes_var.set(self._csv_string(cfg.get("trusted_processes", self.trusted_processes_var.get())))
        self.trusted_domains_var.set(self._csv_string(cfg.get("trusted_domains", self.trusted_domains_var.get())))
        self.web_control_enforce_var.set(self._to_bool(cfg.get("web_control_enforce", self.web_control_enforce_var.get())))
        self.download_shield_var.set(self._to_bool(cfg.get("download_shield_enabled", self.download_shield_var.get())))
        self.download_shield_quarantine_var.set(
            self._to_bool(cfg.get("download_shield_quarantine", self.download_shield_quarantine_var.get()))
        )
        self.exploit_guard_var.set(self._to_bool(cfg.get("exploit_guard_enabled", self.exploit_guard_var.get())))
        self.exploit_guard_auto_kill_var.set(
            self._to_bool(cfg.get("exploit_guard_auto_kill", self.exploit_guard_auto_kill_var.get()))
        )
        self.beacon_guard_var.set(self._to_bool(cfg.get("beacon_guard_enabled", self.beacon_guard_var.get())))
        self.beacon_guard_block_var.set(self._to_bool(cfg.get("beacon_guard_block", self.beacon_guard_block_var.get())))

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
            "policy_mode": self.policy_mode_var.get().strip(),
            "ai_sensitivity": self.ai_sensitivity_var.get(),
            "auto_scan_interval": self.auto_scan_interval_var.get().strip(),
            "notify_manager": bool(self.notify_manager_var.get()),
            "live_sync_interval": self.live_sync_interval_var.get().strip(),
            "sound_alert": bool(self.sound_alert_var.get()),
            "ai_profile": self.ai_profile_var.get().strip(),
            "non_disruptive_mode": bool(self.non_disruptive_mode_var.get()),
            "enforcement_threshold": self.enforcement_threshold_var.get(),
            "block_during_business_hours": bool(self.block_during_business_hours_var.get()),
            "business_hours_start": self.business_hours_start_var.get().strip(),
            "business_hours_end": self.business_hours_end_var.get().strip(),
            "trusted_processes": self.trusted_processes_var.get().strip(),
            "trusted_domains": self.trusted_domains_var.get().strip(),
            "auto_start_on_launch": bool(self.auto_start_on_launch_var.get()),
            "deep_scan_on_start": bool(self.deep_scan_on_start_var.get()),
            "email_risk_alert": bool(self.email_risk_alert_var.get()),
            "web_control_enforce": bool(self.web_control_enforce_var.get()),
            "download_shield_enabled": bool(self.download_shield_var.get()),
            "download_shield_quarantine": bool(self.download_shield_quarantine_var.get()),
            "exploit_guard_enabled": bool(self.exploit_guard_var.get()),
            "exploit_guard_auto_kill": bool(self.exploit_guard_auto_kill_var.get()),
            "beacon_guard_enabled": bool(self.beacon_guard_var.get()),
            "beacon_guard_block": bool(self.beacon_guard_block_var.get()),
        }
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _on_close(self):
        self._cancel_auto_scan()
        self._cancel_admin_live_refresh()
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

