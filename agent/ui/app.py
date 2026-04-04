import ctypes
import tkinter as tk
from tkinter import messagebox, ttk
from pathlib import Path

from PIL import Image, ImageTk

from agent.core.agent import EtheriusAgent
from agent.core.client import enroll_device
from agent.core.config import get_config, update_config
from agent.core.device_info import collect_device_info


class AgentApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Etherius Shield")
        self.root.geometry("980x700")
        self.root.configure(bg="#08111d")
        self.icon_image = None
        self._set_app_identity()
        self.agent = EtheriusAgent(on_status=self.handle_status, on_event=self.handle_event)
        self.status = {}
        self._build()
        self.load_config()
        self.populate_device_info()
        self.root.after(400, self._auto_start_if_ready)

    def _set_app_identity(self):
        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Etherius.Shield")
        except Exception:
            pass

        root_dir = Path(__file__).resolve().parents[2]
        ico_path = root_dir / "suite" / "assets" / "etherius-suite.ico"
        png_path = root_dir / "suite" / "assets" / "etherius-suite.png"

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

    def _build(self):
        top = tk.Frame(self.root, bg="#08111d")
        top.pack(fill="x", padx=24, pady=(24, 12))

        brand_wrap = tk.Frame(top, bg="#08111d")
        brand_wrap.pack(anchor="w")
        self.logo_image = None
        logo_path = Path(__file__).resolve().parent.parent / "assets" / "etherius-logo.jpeg"
        try:
            image = Image.open(logo_path).resize((64, 64))
            self.logo_image = ImageTk.PhotoImage(image)
            tk.Label(brand_wrap, image=self.logo_image, bg="#08111d").pack(side="left", padx=(0, 14))
        except Exception:
            pass
        text_wrap = tk.Frame(brand_wrap, bg="#08111d")
        text_wrap.pack(side="left")
        brand = tk.Label(text_wrap, text="etherius", fg="#f0e8e1", bg="#08111d", font=("Georgia", 28, "bold"))
        brand.pack(anchor="w")
        subtitle = tk.Label(text_wrap, text="Employee Security Client", fg="#8fb2d1", bg="#08111d", font=("Segoe UI", 11))
        subtitle.pack(anchor="w", pady=(4, 0))

        container = tk.Frame(self.root, bg="#08111d")
        container.pack(fill="both", expand=True, padx=24, pady=12)

        left = tk.Frame(container, bg="#0d1828", highlightbackground="#17324d", highlightthickness=1)
        left.pack(side="left", fill="both", expand=True, padx=(0, 10))

        right = tk.Frame(container, bg="#0d1828", highlightbackground="#17324d", highlightthickness=1, width=340)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)

        self._build_left(left)
        self._build_right(right)

    def _build_left(self, parent):
        status_frame = tk.Frame(parent, bg="#0d1828")
        status_frame.pack(fill="x", padx=20, pady=(20, 10))

        self.protection_label = tk.Label(status_frame, text="Protection Offline", fg="#ff8f8f", bg="#0d1828", font=("Segoe UI", 18, "bold"))
        self.protection_label.pack(anchor="w")
        self.detail_label = tk.Label(status_frame, text="Agent is not active yet", fg="#8fb2d1", bg="#0d1828", font=("Segoe UI", 11))
        self.detail_label.pack(anchor="w", pady=(6, 0))

        stats = tk.Frame(parent, bg="#0d1828")
        stats.pack(fill="x", padx=20, pady=10)

        self.stats_vars = {
            "events_sent": tk.StringVar(value="0"),
            "events_failed": tk.StringVar(value="0"),
            "heartbeat": tk.StringVar(value="Unknown"),
            "last_event": tk.StringVar(value="-"),
        }
        cards = [
            ("Events Sent", self.stats_vars["events_sent"]),
            ("Failed Sends", self.stats_vars["events_failed"]),
            ("Heartbeat", self.stats_vars["heartbeat"]),
            ("Last Event", self.stats_vars["last_event"]),
        ]
        for idx, (label, var) in enumerate(cards):
            card = tk.Frame(stats, bg="#122339", highlightbackground="#1b3d5e", highlightthickness=1)
            card.grid(row=idx // 2, column=idx % 2, padx=6, pady=6, sticky="nsew")
            stats.grid_columnconfigure(idx % 2, weight=1)
            tk.Label(card, text=label, fg="#8fb2d1", bg="#122339", font=("Segoe UI", 10)).pack(anchor="w", padx=14, pady=(12, 4))
            tk.Label(card, textvariable=var, fg="#eef5ff", bg="#122339", font=("Segoe UI", 18, "bold")).pack(anchor="w", padx=14, pady=(0, 12))

        actions = tk.Frame(parent, bg="#0d1828")
        actions.pack(fill="x", padx=20, pady=10)
        ttk.Button(actions, text="Start Protection", command=self.start_agent).pack(side="left", padx=(0, 8))
        ttk.Button(actions, text="Stop Protection", command=self.stop_agent).pack(side="left")

        feed_wrap = tk.Frame(parent, bg="#0d1828")
        feed_wrap.pack(fill="both", expand=True, padx=20, pady=(10, 20))
        tk.Label(feed_wrap, text="Protection Activity", fg="#eef5ff", bg="#0d1828", font=("Segoe UI", 13, "bold")).pack(anchor="w", pady=(0, 8))
        self.feed = tk.Text(feed_wrap, bg="#08111d", fg="#d9e8f7", relief="flat", insertbackground="#d9e8f7", font=("Consolas", 10))
        self.feed.pack(fill="both", expand=True)

    def _build_right(self, parent):
        tk.Label(parent, text="Activation", fg="#eef5ff", bg="#0d1828", font=("Segoe UI", 14, "bold")).pack(anchor="w", padx=18, pady=(20, 6))
        tk.Label(parent, text="Paste the activation code from the manager dashboard or fill the fields manually.", fg="#8fb2d1", bg="#0d1828", wraplength=290, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=18)

        self.activation_code = tk.StringVar()
        self.company_code = tk.StringVar()
        self.employee_key = tk.StringVar()
        self.backend_url = tk.StringVar()
        self.endpoint_id = tk.StringVar()
        self.agent_token = tk.StringVar()
        self.device_name = tk.StringVar()
        self.device_os = tk.StringVar()
        self.device_ip = tk.StringVar()
        self.device_mac = tk.StringVar()
        self.email_sender = tk.StringVar()
        self.email_subject = tk.StringVar()

        self._entry(parent, "Company Enrollment Code", self.company_code)
        self._entry(parent, "Employee License Key", self.employee_key)
        self._entry(parent, "Activation Code", self.activation_code)
        ttk.Button(parent, text="Enroll This Device", command=self.enroll_this_device).pack(fill="x", padx=18, pady=(4, 8))
        ttk.Button(parent, text="Apply Activation Code", command=self.apply_activation_code).pack(fill="x", padx=18, pady=(4, 10))

        self._entry(parent, "Backend URL", self.backend_url)
        self._entry(parent, "Endpoint ID", self.endpoint_id)
        self._entry(parent, "Agent Token", self.agent_token, show="*")
        self._entry(parent, "Detected Device Name", self.device_name)
        self._entry(parent, "Detected Operating System", self.device_os)
        self._entry(parent, "Detected IP", self.device_ip)
        self._entry(parent, "Detected MAC", self.device_mac)

        ttk.Button(parent, text="Save Connection", command=self.save_connection).pack(fill="x", padx=18, pady=(8, 18))

        tk.Label(parent, text="Malicious Email Check", fg="#eef5ff", bg="#0d1828", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(10, 8))
        self._entry(parent, "Sender", self.email_sender)
        self._entry(parent, "Subject", self.email_subject)
        tk.Label(parent, text="Email Body / URL", fg="#8fb2d1", bg="#0d1828", font=("Segoe UI", 10)).pack(anchor="w", padx=18, pady=(10, 6))
        self.email_body = tk.Text(parent, height=6, bg="#08111d", fg="#eef5ff", insertbackground="#eef5ff", relief="flat", font=("Segoe UI", 10))
        self.email_body.pack(fill="x", padx=18)
        ttk.Button(parent, text="Analyze Suspicious Email", command=self.analyze_email).pack(fill="x", padx=18, pady=(8, 18))

        tk.Label(parent, text="What this software does", fg="#eef5ff", bg="#0d1828", font=("Segoe UI", 13, "bold")).pack(anchor="w", padx=18, pady=(10, 8))
        info = (
            "This employee app monitors process, network, file, and login activity on the local device.\n\n"
            "It sends telemetry to Etherius so managers can see endpoint health, alerts, and response actions in the dashboard.\n\n"
            "Users do not need dashboard access. They only need this client installed and activated."
        )
        tk.Label(parent, text=info, fg="#8fb2d1", bg="#0d1828", wraplength=290, justify="left", font=("Segoe UI", 10)).pack(anchor="w", padx=18)

    def _entry(self, parent, label, variable, show=None):
        wrap = tk.Frame(parent, bg="#0d1828")
        wrap.pack(fill="x", padx=18, pady=(10, 0))
        tk.Label(wrap, text=label, fg="#8fb2d1", bg="#0d1828", font=("Segoe UI", 10)).pack(anchor="w", pady=(0, 6))
        entry = tk.Entry(wrap, textvariable=variable, show=show, bg="#08111d", fg="#eef5ff", insertbackground="#eef5ff", relief="flat", font=("Segoe UI", 10))
        entry.pack(fill="x", ipady=8)

    def load_config(self):
        config = get_config()
        self.company_code.set(config.get("company_code", ""))
        self.employee_key.set(config.get("employee_key", ""))
        self.activation_code.set(config.get("activation_code", ""))
        self.backend_url.set(config.get("backend_url", ""))
        self.endpoint_id.set(config.get("endpoint_id", ""))
        self.agent_token.set(config.get("agent_token", ""))
    def populate_device_info(self):
        info = collect_device_info()
        self.device_name.set(info["hostname"])
        self.device_os.set(info["os"])
        self.device_ip.set(info["ip_address"])
        self.device_mac.set(info["mac_address"])

    def save_connection(self):
        self.save_connection_with_options(notify=True)

    def save_connection_with_options(self, notify=True):
        update_config({
            "company_code": self.company_code.get().strip(),
            "employee_key": self.employee_key.get().strip(),
            "activation_code": self.activation_code.get().strip(),
            "backend_url": self.backend_url.get().strip(),
            "endpoint_id": self.endpoint_id.get().strip(),
            "agent_token": self.agent_token.get().strip(),
        })
        if notify:
            messagebox.showinfo("Etherius Shield", "Connection settings saved.")

    def apply_activation_code(self):
        code = self.activation_code.get().strip()
        parts = code.split("|")
        if len(parts) != 3:
            messagebox.showerror("Invalid Code", "Activation code format should be backend_url|endpoint_id|agent_token")
            return
        backend_url, endpoint_id, agent_token = parts
        self.backend_url.set(backend_url)
        self.endpoint_id.set(endpoint_id)
        self.agent_token.set(agent_token)
        self.save_connection_with_options(notify=False)

    def enroll_this_device(self):
        code = self.company_code.get().strip()
        backend_url = self.backend_url.get().strip() or "http://localhost:8000"
        if not code:
            messagebox.showerror("Missing Code", "Enter the company enrollment code from the manager dashboard.")
            return
        employee_key = self.employee_key.get().strip()
        if not employee_key:
            messagebox.showerror("Missing Employee Key", "Enter the employee license key provided by your administrator.")
            return
        payload = {
            "company_code": code,
            "employee_key": employee_key,
            **collect_device_info(),
        }
        try:
            response = enroll_device(payload, backend_url=backend_url)
            response.raise_for_status()
            data = response.json()
            self.activation_code.set(data["activation_code"])
            self.apply_activation_code()
            self.append_feed("Device enrolled successfully with company code.")
            self.start_agent(silent=True)
        except Exception as error:
            messagebox.showerror("Enrollment Failed", str(error))

    def _has_valid_connection_config(self):
        endpoint_id = self.endpoint_id.get().strip()
        agent_token = self.agent_token.get().strip()
        backend_url = self.backend_url.get().strip()
        placeholders = {"PASTE_YOUR_AGENT_TOKEN_HERE", "PASTE_YOUR_ENDPOINT_ID_HERE", ""}
        if endpoint_id in placeholders or agent_token in placeholders:
            return False
        return bool(backend_url and endpoint_id and agent_token)

    def _auto_start_if_ready(self):
        if self._has_valid_connection_config() and not self.agent.running:
            self.start_agent(silent=True)

    def start_agent(self, silent=False):
        if not self._has_valid_connection_config() and self.activation_code.get().strip():
            self.apply_activation_code()
        if not self._has_valid_connection_config():
            if not silent:
                messagebox.showerror(
                    "Connection Required",
                    "Enroll this device first, or paste a valid activation code before starting protection.",
                )
            self.append_feed("Protection not started. Missing enrollment/activation details.")
            return
        self.save_connection_with_options(notify=False)
        self.agent.start()
        self.append_feed("Protection engine started.")

    def stop_agent(self):
        self.agent.stop()
        self.append_feed("Protection engine stopped.")
        self.protection_label.configure(text="Protection Offline", fg="#ff8f8f")

    def handle_status(self, status):
        self.root.after(0, lambda: self._apply_status(status))

    def _apply_status(self, status):
        self.status = status
        self.stats_vars["events_sent"].set(str(status.get("events_sent", 0)))
        self.stats_vars["events_failed"].set(str(status.get("events_failed", 0)))
        self.stats_vars["heartbeat"].set("Connected" if status.get("heartbeat_ok") else "Waiting")
        self.stats_vars["last_event"].set(status.get("last_event_time", "-") or "-")
        if self.agent.running:
            self.protection_label.configure(text="Protection Active", fg="#7ce2b8")
            self.detail_label.configure(text="Telemetry is being collected and forwarded to the manager dashboard.")

    def handle_event(self, item):
        self.root.after(0, lambda: self.append_feed(self._format_event(item)))

    def _format_event(self, item):
        kind = item.get("kind", "event").upper()
        event_type = item.get("event_type", "unknown")
        detail = item.get("error") or item.get("status_code") or ""
        return f"[{kind}] {event_type} {detail}".strip()

    def append_feed(self, text):
        self.feed.insert("end", f"{text}\n")
        self.feed.see("end")

    def analyze_email(self):
        payload = {
            "sender": self.email_sender.get().strip(),
            "subject": self.email_subject.get().strip(),
            "body": self.email_body.get("1.0", "end").strip(),
            "hostname": self.device_name.get().strip(),
        }
        if not payload["body"] and not payload["subject"]:
            messagebox.showerror("Missing Input", "Paste the suspicious email content first.")
            return
        self.agent.submit_manual_event({
            "event_type": "email",
            "severity": "info",
            "payload": payload,
        })
        self.append_feed("Suspicious email submitted for analysis.")


def main():
    root = tk.Tk()
    style = ttk.Style()
    style.theme_use("clam")
    style.configure("TButton", padding=8)
    app = AgentApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
