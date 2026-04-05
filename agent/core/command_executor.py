import os
import subprocess
import threading
import time
import tkinter as tk
from tkinter import messagebox

from agent.core.client import get_commands, send_command_result


class CommandExecutor:
    def __init__(self, on_event=None):
        self.running = False
        self.on_event = on_event

    def _emit(self, kind, detail):
        if self.on_event:
            try:
                self.on_event({"kind": kind, "event_type": "remote_command", "detail": detail})
            except Exception:
                pass

    def _lock_screen(self):
        if os.name != "nt":
            return False, "lock_screen is supported on Windows only"
        try:
            subprocess.run(
                ["rundll32.exe", "user32.dll,LockWorkStation"],
                capture_output=True,
                timeout=6,
            )
            return True, "Screen lock executed"
        except Exception as error:
            return False, str(error)

    def _show_message(self, message: str):
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showinfo("Etherius Security Notice", message[:500] or "Security instruction received.")
            root.destroy()
            return True, "Message shown"
        except Exception as error:
            return False, str(error)

    def _restart_agent(self):
        # Soft acknowledgement; full process restart can be orchestrated by launcher/service.
        return True, "Restart requested (requires launcher/service integration)"

    def _execute(self, command):
        command_type = str(command.get("command_type", "")).strip().lower()
        payload = command.get("payload", {}) or {}
        if command_type == "lock_screen":
            return self._lock_screen()
        if command_type == "show_message":
            return self._show_message(str(payload.get("message", "")))
        if command_type == "restart_agent":
            return self._restart_agent()
        return False, f"Unsupported command: {command_type}"

    def _poll_once(self):
        try:
            response = get_commands(timeout=12)
            response.raise_for_status()
            commands = response.json() or []
        except Exception as error:
            self._emit("failed", f"command poll failed: {error}")
            return

        for command in commands:
            command_id = command.get("id")
            if not command_id:
                continue
            ok, result = self._execute(command)
            status = "executed" if ok else "failed"
            try:
                send_command_result(command_id, status=status, result_text=result, timeout=12)
            except Exception:
                pass
            self._emit("system", f"{command.get('command_type')} -> {status}: {result}")

    def start(self):
        self.running = True

        def loop():
            while self.running:
                self._poll_once()
                time.sleep(30)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
