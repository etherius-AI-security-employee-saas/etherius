import os
import platform
import queue
import threading
import time
from datetime import datetime

from agent.collectors.file_monitor import FileMonitor
from agent.collectors.login_monitor import LoginMonitor
from agent.collectors.network_monitor import NetworkMonitor
from agent.collectors.process_monitor import ProcessMonitor
from agent.core.client import send_event
from agent.core.heartbeat import Heartbeat

event_queue = queue.Queue()


class EtheriusAgent:
    def __init__(self, on_status=None, on_event=None):
        self.running = False
        self.on_status = on_status
        self.on_event = on_event
        self.stats = {
            "events_sent": 0,
            "events_failed": 0,
            "last_event_time": None,
            "last_error": None,
            "last_heartbeat": None,
            "heartbeat_ok": False,
        }
        self.heartbeat = Heartbeat(on_result=self._handle_heartbeat)
        self.collectors = [
            ProcessMonitor(event_queue),
            NetworkMonitor(event_queue),
            LoginMonitor(event_queue),
            FileMonitor(event_queue),
        ]

    def _emit_status(self):
        if self.on_status:
            self.on_status(dict(self.stats))

    def _emit_event(self, item):
        if self.on_event:
            self.on_event(item)

    def _handle_heartbeat(self, ok, status_code, error):
        self.stats["heartbeat_ok"] = ok
        self.stats["last_heartbeat"] = datetime.utcnow().isoformat()
        self.stats["last_error"] = error if not ok else self.stats["last_error"]
        self._emit_status()

    def _send(self, event):
        try:
            response = send_event(event)
            self.stats["events_sent"] += 1
            self.stats["last_event_time"] = datetime.utcnow().isoformat()
            self.stats["last_error"] = None
            self._emit_event({
                "kind": "sent",
                "event_type": event.get("event_type"),
                "status_code": response.status_code,
                "time": self.stats["last_event_time"],
            })
        except Exception as error:
            self.stats["events_failed"] += 1
            self.stats["last_error"] = str(error)
            self._emit_event({
                "kind": "failed",
                "event_type": event.get("event_type"),
                "error": str(error),
                "time": datetime.utcnow().isoformat(),
            })
        finally:
            self._emit_status()

    def _session_payload(self):
        username = ""
        try:
            username = os.getlogin()
        except Exception:
            username = os.environ.get("USERNAME", "unknown")
        return {
            "username": username,
            "platform": platform.system(),
            "hour_of_day": datetime.now().hour,
        }

    def _sender_loop(self):
        while self.running:
            try:
                event = event_queue.get(timeout=5)
                self._emit_event({
                    "kind": "captured",
                    "event_type": event.get("event_type"),
                    "time": datetime.utcnow().isoformat(),
                })
                self._send(event)
            except queue.Empty:
                continue

    def start(self):
        if self.running:
            return
        self.running = True
        self.heartbeat.start()
        for collector in self.collectors:
            collector.start()
        threading.Thread(target=self._sender_loop, daemon=True).start()
        self._send({
            "event_type": "employee_login",
            "severity": "info",
            "payload": self._session_payload(),
        })
        self._emit_event({
            "kind": "system",
            "event_type": "agent_started",
            "time": datetime.utcnow().isoformat(),
        })
        self._emit_status()

    def submit_manual_event(self, event):
        self._emit_event({
            "kind": "captured",
            "event_type": event.get("event_type"),
            "time": datetime.utcnow().isoformat(),
        })
        self._send(event)

    def stop(self):
        if not self.running:
            return
        self._send({
            "event_type": "employee_logout",
            "severity": "info",
            "payload": self._session_payload(),
        })
        self.running = False
        self.heartbeat.stop()
        for collector in self.collectors:
            collector.stop()
        self._emit_event({
            "kind": "system",
            "event_type": "agent_stopped",
            "time": datetime.utcnow().isoformat(),
        })
        self._emit_status()


if __name__ == "__main__":
    agent = EtheriusAgent()
    agent.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        agent.stop()
