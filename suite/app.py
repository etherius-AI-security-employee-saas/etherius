import ctypes
import os
import subprocess
import tkinter as tk
import urllib.error
import urllib.request
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import ttk

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "suite" / "assets"
CLOUD_DASHBOARD_URL = os.getenv("ETHERIUS_DASHBOARD_URL", "https://etherius-security-dashboard.vercel.app")
CLOUD_API_HEALTH_URL = os.getenv("ETHERIUS_API_HEALTH_URL", "https://etherius-security-api.vercel.app/health")
LOCAL_DASHBOARD_URL = "http://127.0.0.1:8000/dashboard"
LOCAL_API_HEALTH_URL = "http://127.0.0.1:8000/health"


class EtheriusSuiteApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Etherius Command Suite")
        self.root.geometry("1360x880")
        self.root.minsize(1220, 780)
        self.root.configure(bg="#070612")
        self.icon_image = None
        self.health_items = {}
        self.log_widget = None
        self.use_local_backend = os.getenv("ETHERIUS_LOCAL_BACKEND", "").strip() == "1"
        self.dashboard_url = LOCAL_DASHBOARD_URL if self.use_local_backend else CLOUD_DASHBOARD_URL
        self.health_url = LOCAL_API_HEALTH_URL if self.use_local_backend else CLOUD_API_HEALTH_URL

        self._set_app_identity()
        self._configure_styles()
        self._build()
        if self.use_local_backend:
            self._start_backend_service()
            self.root.after(1200, lambda: self._open_dashboard_when_ready(attempt=0))
        else:
            self._open_url(self.dashboard_url)
        self._refresh_health()

    def _set_app_identity(self):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Etherius.CommandSuite")
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

        style.configure(
            "Etherius.Primary.TButton",
            padding=(16, 12),
            font=("Segoe UI", 10, "bold"),
            foreground="#ffffff",
            background="#8d58ff",
            borderwidth=0,
        )
        style.map("Etherius.Primary.TButton", background=[("active", "#9f6bff"), ("pressed", "#7946e6")])

        style.configure(
            "Etherius.Secondary.TButton",
            padding=(16, 12),
            font=("Segoe UI", 10, "bold"),
            foreground="#ece2ff",
            background="#1a1635",
            borderwidth=0,
        )
        style.map("Etherius.Secondary.TButton", background=[("active", "#241e4a"), ("pressed", "#151133")])

    def _build(self):
        shell = tk.Frame(self.root, bg="#070612")
        shell.pack(fill="both", expand=True, padx=24, pady=20)

        self._build_hero(shell)

        body = tk.Frame(shell, bg="#070612")
        body.pack(fill="both", expand=True, pady=(12, 0))

        left = tk.Frame(body, bg="#070612")
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(body, bg="#070612", width=430)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._build_launch_panel(left)
        self._build_health_panel(left)
        self._build_activity_panel(left)

        self._build_admin_panel(right)
        self._build_employee_panel(right)

    def _build_hero(self, parent):
        card = tk.Frame(parent, bg="#141028", highlightbackground="#5d46aa", highlightthickness=1)
        card.pack(fill="x")

        row = tk.Frame(card, bg="#141028")
        row.pack(fill="x", padx=24, pady=20)

        mark = tk.Canvas(row, width=92, height=92, bg="#141028", highlightthickness=0)
        mark.pack(side="left", padx=(0, 16))
        mark.create_oval(5, 5, 87, 87, fill="#1a1840", outline="#9273ff", width=3)
        mark.create_oval(20, 20, 72, 72, fill="#0f0f24", outline="#4ddfff", width=2)
        mark.create_text(46, 45, text="e", fill="#f5f0ff", font=("Rajdhani", 38, "bold"))

        text_col = tk.Frame(row, bg="#141028")
        text_col.pack(side="left", fill="both", expand=True)

        tk.Label(text_col, text="etherius", fg="#f6f2ff", bg="#141028", font=("Rajdhani", 34, "bold")).pack(anchor="w")
        tk.Label(
            text_col,
            text="Professional security suite for managed endpoint protection, license-controlled enrollment, and real-time operations.",
            fg="#c2b7e5",
            bg="#141028",
            font=("Segoe UI", 11),
        ).pack(anchor="w", pady=(6, 0))

        badge_row = tk.Frame(text_col, bg="#141028")
        badge_row.pack(anchor="w", pady=(12, 0))
        self._badge(badge_row, "Admin Subscription", "#211a43", "#d7c9ff").pack(side="left", padx=(0, 8))
        self._badge(badge_row, "Employee License Keys", "#132a3d", "#b8f2ff").pack(side="left", padx=(0, 8))
        self._badge(badge_row, "Taskbar Branded App", "#2e153e", "#ffcff0").pack(side="left")

    def _build_launch_panel(self, parent):
        card = self._card(parent, "Launch Center", "Open customer dashboard and protection workspace in one click.")
        card.pack(fill="x", pady=(0, 10))

        grid = tk.Frame(card, bg="#141028")
        grid.pack(fill="x", padx=16, pady=(8, 14))

        self._tile(grid, "Start Full Platform", "Open dashboard and ready all customer controls", self._start_full_suite, primary=True).grid(row=0, column=0, sticky="nsew", padx=6, pady=6)
        self._tile(grid, "Open Dashboard", "Customer admin command center", lambda: self._open_url(self.dashboard_url)).grid(row=0, column=1, sticky="nsew", padx=6, pady=6)
        self._tile(grid, "Open Employee Shield", "Run desktop protection client", self._open_employee_shield).grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self._tile(grid, "Open API Health", "Live backend status endpoint", lambda: self._open_url(self.health_url)).grid(row=1, column=1, sticky="nsew", padx=6, pady=6)

        for col in range(2):
            grid.grid_columnconfigure(col, weight=1)

    def _build_health_panel(self, parent):
        card = self._card(parent, "Platform Health", "Live status of dashboard and API availability.")
        card.pack(fill="x", pady=(0, 10))

        body = tk.Frame(card, bg="#141028")
        body.pack(fill="x", padx=16, pady=(8, 14))

        self.health_items["Backend API"] = self._health_row(body, "Backend API", self.health_url)
        self.health_items["Dashboard"] = self._health_row(body, "Dashboard", self.dashboard_url)
        self.health_items["API Docs"] = self._health_row(body, "Shield Enrollment", f"{self.health_url.replace('/health', '')}/api/agent/enroll")

        actions = tk.Frame(body, bg="#141028")
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Refresh Status", command=self._refresh_health, style="Etherius.Secondary.TButton").pack(side="left")

    def _build_activity_panel(self, parent):
        card = self._card(parent, "Operations Feed", "Recent launcher activity for your local environment.")
        card.pack(fill="both", expand=True)

        body = tk.Frame(card, bg="#141028")
        body.pack(fill="both", expand=True, padx=16, pady=(8, 14))

        self.log_widget = tk.Text(body, height=10, bg="#0b0920", fg="#e7deff", relief="flat", font=("Consolas", 10), insertbackground="#e7deff")
        self.log_widget.pack(fill="both", expand=True)
        self._log(f"Etherius Command Suite is ready ({'local' if self.use_local_backend else 'cloud'} mode).")

    def _build_admin_panel(self, parent):
        card = self._card(parent, "Admin Workspace", "Subscription owner controls and manager workflow.")
        card.pack(fill="x", pady=(0, 10))

        for step in [
            "1) Open customer dashboard from Launch Center.",
            "2) Register/login with a valid subscription key.",
            "3) Generate employee license keys in Settings.",
            "4) Share enrollment code + employee key with staff.",
        ]:
            self._bullet(card, step)

        actions = tk.Frame(card, bg="#141028")
        actions.pack(fill="x", padx=16, pady=(10, 14))
        ttk.Button(actions, text="Open Start Guide", command=lambda: self._open_file("TUTORIALS/START_HERE.md"), style="Etherius.Secondary.TButton").pack(fill="x", pady=4)

    def _build_employee_panel(self, parent):
        card = self._card(parent, "Employee Workspace", "Installer-side deployment flow for customer devices.")
        card.pack(fill="both", expand=True)

        for step in [
            "1) Install Etherius Shield on employee machine.",
            "2) Paste company enrollment code and employee key.",
            "3) Click Enroll Device and Start Protection.",
            "4) Device appears live in endpoint fleet dashboard.",
        ]:
            self._bullet(card, step)

        actions = tk.Frame(card, bg="#141028")
        actions.pack(fill="x", padx=16, pady=(10, 14))
        ttk.Button(actions, text="Open Employee Shield", command=self._open_employee_shield, style="Etherius.Primary.TButton").pack(fill="x", pady=4)
        ttk.Button(actions, text="Open Start Guide", command=lambda: self._open_file("TUTORIALS/START_HERE.md"), style="Etherius.Secondary.TButton").pack(fill="x", pady=4)

    def _card(self, parent, title, subtitle):
        card = tk.Frame(parent, bg="#141028", highlightbackground="#524197", highlightthickness=1)
        tk.Label(card, text=title, fg="#f4f0ff", bg="#141028", font=("Segoe UI", 16, "bold")).pack(anchor="w", padx=16, pady=(14, 4))
        tk.Label(card, text=subtitle, fg="#b6a9dd", bg="#141028", font=("Segoe UI", 10), wraplength=640, justify="left").pack(anchor="w", padx=16)
        return card

    def _badge(self, parent, text, bg, fg):
        return tk.Label(parent, text=text, bg=bg, fg=fg, font=("Segoe UI", 9, "bold"), padx=10, pady=5)

    def _tile(self, parent, title, text, command, primary=False):
        bg = "#242050" if primary else "#171436"
        tile = tk.Frame(parent, bg=bg, highlightbackground="#5a48a0", highlightthickness=1)
        tk.Label(tile, text=title, fg="#ffffff", bg=bg, font=("Segoe UI", 11, "bold")).pack(anchor="w", padx=14, pady=(14, 6))
        tk.Label(tile, text=text, fg="#d4c9f2", bg=bg, font=("Segoe UI", 9)).pack(anchor="w", padx=14)
        ttk.Button(tile, text="Open", command=command, style="Etherius.Primary.TButton" if primary else "Etherius.Secondary.TButton").pack(anchor="w", padx=14, pady=14)
        return tile

    def _bullet(self, parent, text):
        row = tk.Frame(parent, bg="#141028")
        row.pack(fill="x", padx=16, pady=(10, 0))
        dot = tk.Canvas(row, width=14, height=14, bg="#141028", highlightthickness=0)
        dot.pack(side="left", padx=(0, 8), pady=(3, 0))
        dot.create_oval(3, 3, 11, 11, fill="#8f67ff", outline="")
        tk.Label(row, text=text, fg="#e1d8ff", bg="#141028", font=("Segoe UI", 10), wraplength=360, justify="left").pack(side="left", fill="x", expand=True)

    def _health_row(self, parent, label, value):
        box = tk.Frame(parent, bg="#1a1638", highlightbackground="#4f3f8f", highlightthickness=1)
        box.pack(fill="x", pady=4)
        tk.Label(box, text=label, fg="#b4a7df", bg="#1a1638", font=("Segoe UI", 9)).pack(side="left", padx=10, pady=10)
        tk.Label(box, text=value, fg="#ebe3ff", bg="#1a1638", font=("Segoe UI", 10, "bold")).pack(side="left", padx=(0, 10))
        status = tk.Label(box, text="Checking...", fg="#ffdcab", bg="#1a1638", font=("Segoe UI", 9, "bold"))
        status.pack(side="right", padx=10)
        return status

    def _start_full_suite(self):
        if self.use_local_backend:
            self._start_backend_service()
            self.root.after(2000, lambda: self._open_url(self.dashboard_url))
            return
        self._open_url(self.dashboard_url)

    def _start_backend_service(self):
        if self._port_open("127.0.0.1", 8000):
            self._log("Backend already running.")
            return

        backend_python = ROOT / "backend" / "venv" / "Scripts" / "python.exe"
        if backend_python.exists():
            subprocess.Popen(
                [
                    "cmd",
                    "/c",
                    "start",
                    "",
                    "/min",
                    "cmd",
                    "/k",
                    f"cd /d \"{ROOT / 'backend'}\" && venv\\Scripts\\python.exe run_backend.py",
                ],
                cwd=str(ROOT),
            )
            self._log("Backend runtime launched from Python environment.")
            return

        backend_exe = ROOT / "release" / "bin" / "EtheriusBackendService.exe"
        if backend_exe.exists():
            subprocess.Popen([str(backend_exe)], cwd=str(ROOT))
            self._log("Backend service executable launched.")
            return

        self._log("Backend runtime missing. Install backend dependencies first.")

    def _open_employee_shield(self):
        shield_exe = ROOT / "release" / "bin" / "EtheriusShield.exe"
        if shield_exe.exists():
            subprocess.Popen([str(shield_exe)], cwd=str(ROOT))
            self._log("Opened employee shield executable.")
            return
        subprocess.Popen(["python", "-m", "agent.ui.app"], cwd=str(ROOT))
        self._log("Opened employee shield.")

    def _open_file(self, name):
        path = ROOT / name
        subprocess.Popen(["cmd", "/c", "start", "", str(path)], cwd=str(ROOT))
        self._log(f"Opened file: {name}")

    def _open_url(self, url):
        webbrowser.open(url)
        self._log(f"Opened URL: {url}")

    def _open_dashboard_when_ready(self, attempt=0):
        if self._port_open("127.0.0.1", 8000):
            self._open_url(self.dashboard_url)
            return
        if attempt >= 15:
            self._log("Backend startup is taking longer than expected.")
            return
        self.root.after(1000, lambda: self._open_dashboard_when_ready(attempt + 1))

    def _port_open(self, host, port, timeout=0.7):
        try:
            import socket

            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def _url_online(self, url, timeout=4):
        try:
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=timeout) as response:
                return 200 <= response.status < 500
        except urllib.error.HTTPError as http_error:
            return 200 <= http_error.code < 500
        except Exception:
            return False

    def _refresh_health(self):
        if self.use_local_backend:
            backend_ok = self._port_open("127.0.0.1", 8000)
            dashboard_ok = backend_ok
            enroll_ok = backend_ok
        else:
            backend_ok = self._url_online(self.health_url)
            dashboard_ok = self._url_online(self.dashboard_url)
            enroll_ok = self._url_online(f"{self.health_url.replace('/health', '')}/api/agent/enroll")

        self._set_health("Backend API", backend_ok)
        self._set_health("Dashboard", dashboard_ok)
        self._set_health("API Docs", enroll_ok)

        self.root.after(7000, self._refresh_health)

    def _set_health(self, key, ok):
        label = self.health_items.get(key)
        if not label:
            return
        label.configure(text="Online" if ok else "Offline", fg="#7fe4ba" if ok else "#ff9f9f")

    def _log(self, text):
        if not self.log_widget:
            return
        now = datetime.now().strftime("%H:%M:%S")
        self.log_widget.insert("end", f"[{now}] {text}\n")
        self.log_widget.see("end")


def main():
    root = tk.Tk()
    EtheriusSuiteApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
