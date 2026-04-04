import tkinter as tk
from tkinter import messagebox, ttk

import requests


class CEOConsole:
    def __init__(self, root):
        self.root = root
        self.root.title("Etherius CEO Control Console")
        self.root.geometry("1120x760")
        self.root.configure(bg="#0c0a1d")
        self._build()

    def _build(self):
        shell = tk.Frame(self.root, bg="#0c0a1d")
        shell.pack(fill="both", expand=True, padx=18, pady=16)

        title = tk.Label(
            shell,
            text="ETHERIUS CEO CONTROL",
            font=("Segoe UI", 22, "bold"),
            fg="#f5f0ff",
            bg="#0c0a1d",
        )
        title.pack(anchor="w", pady=(0, 10))

        config = tk.Frame(shell, bg="#161332", highlightbackground="#514293", highlightthickness=1)
        config.pack(fill="x", pady=(0, 10))
        self.api_url = tk.StringVar(value="https://etherius-security-api.vercel.app")
        self.ceo_key = tk.StringVar()
        self._entry_row(config, "API Base URL", self.api_url)
        self._entry_row(config, "CEO Master Key", self.ceo_key, show="*")

        issue = tk.Frame(shell, bg="#161332", highlightbackground="#514293", highlightthickness=1)
        issue.pack(fill="x", pady=(0, 10))
        tk.Label(issue, text="Issue Customer Subscription", font=("Segoe UI", 14, "bold"), fg="#f0e8ff", bg="#161332").pack(anchor="w", padx=14, pady=(10, 2))
        issue_form = tk.Frame(issue, bg="#161332")
        issue_form.pack(fill="x", padx=14, pady=(0, 10))
        self.label = tk.StringVar(value="Customer Subscription")
        self.employee_limit = tk.StringVar(value="300")
        self.valid_days = tk.StringVar(value="365")
        self.max_activations = tk.StringVar(value="1")
        self._entry_row(issue_form, "Label", self.label)
        self._entry_row(issue_form, "Employee Seat Limit", self.employee_limit)
        self._entry_row(issue_form, "Valid Days", self.valid_days)
        self._entry_row(issue_form, "Company Activations", self.max_activations)

        ttk.Button(issue_form, text="Issue Subscription Key", command=self.issue_key).pack(anchor="w", pady=8)
        self.issue_output = tk.Text(issue_form, height=4, bg="#0b0921", fg="#ece2ff", relief="flat")
        self.issue_output.pack(fill="x", pady=(6, 0))

        customers = tk.Frame(shell, bg="#161332", highlightbackground="#514293", highlightthickness=1)
        customers.pack(fill="both", expand=True)
        top = tk.Frame(customers, bg="#161332")
        top.pack(fill="x", padx=14, pady=(10, 8))
        tk.Label(top, text="Customer Fleet Overview", font=("Segoe UI", 14, "bold"), fg="#f0e8ff", bg="#161332").pack(side="left")
        ttk.Button(top, text="Refresh Customers", command=self.refresh_customers).pack(side="right")

        cols = ("company", "status", "seats", "used", "remaining", "online", "alerts", "logins", "logouts")
        self.table = ttk.Treeview(customers, columns=cols, show="headings")
        for col, name, width in [
            ("company", "Company", 230),
            ("status", "Subscription", 110),
            ("seats", "Seat Limit", 80),
            ("used", "Employees", 80),
            ("remaining", "Remaining", 90),
            ("online", "Online", 70),
            ("alerts", "Open Alerts", 80),
            ("logins", "Logins Today", 95),
            ("logouts", "Logouts Today", 95),
        ]:
            self.table.heading(col, text=name)
            self.table.column(col, width=width, anchor="center")
        self.table.column("company", anchor="w")
        self.table.pack(fill="both", expand=True, padx=14, pady=(0, 14))

    def _entry_row(self, parent, label, var, show=None):
        row = tk.Frame(parent, bg=parent["bg"])
        row.pack(fill="x", pady=4)
        tk.Label(row, text=label, width=20, anchor="w", fg="#c4b8e8", bg=parent["bg"]).pack(side="left")
        tk.Entry(row, textvariable=var, show=show, bg="#0d0b24", fg="#f1e9ff", insertbackground="#f1e9ff", relief="flat").pack(side="left", fill="x", expand=True, ipady=5)

    def _headers(self):
        key = self.ceo_key.get().strip()
        if not key:
            raise ValueError("CEO Master Key is required")
        return {"x-ceo-key": key, "Content-Type": "application/json"}

    def issue_key(self):
        try:
            payload = {
                "label": self.label.get().strip() or "Customer Subscription",
                "employee_limit": max(1, int(self.employee_limit.get().strip() or "1")),
                "valid_days": max(1, int(self.valid_days.get().strip() or "1")),
                "max_activations": max(1, int(self.max_activations.get().strip() or "1")),
            }
            url = f"{self.api_url.get().strip().rstrip('/')}/api/licenses/subscription/issue"
            response = requests.post(url, json=payload, headers=self._headers(), timeout=20)
            response.raise_for_status()
            data = response.json()
            self.issue_output.delete("1.0", "end")
            self.issue_output.insert("1.0", f"Subscription Key: {data.get('key_value')}\nExpires: {data.get('expires_at')}\nSeat Limit: {data.get('seat_limit')}")
        except Exception as exc:
            messagebox.showerror("Issue Failed", str(exc))

    def refresh_customers(self):
        try:
            url = f"{self.api_url.get().strip().rstrip('/')}/api/licenses/ceo/customers"
            response = requests.get(url, headers=self._headers(), timeout=20)
            response.raise_for_status()
            rows = response.json()
            for child in self.table.get_children():
                self.table.delete(child)
            for item in rows:
                self.table.insert(
                    "",
                    "end",
                    values=(
                        item.get("company_name"),
                        item.get("subscription_status"),
                        item.get("seat_limit"),
                        item.get("employees_used"),
                        item.get("employees_remaining"),
                        item.get("online_endpoints"),
                        item.get("open_alerts"),
                        item.get("login_events_today"),
                        item.get("logout_events_today"),
                    ),
                )
        except Exception as exc:
            messagebox.showerror("Refresh Failed", str(exc))


def main():
    root = tk.Tk()
    style = ttk.Style()
    try:
        style.theme_use("clam")
    except Exception:
        pass
    CEOConsole(root)
    root.mainloop()


if __name__ == "__main__":
    main()
