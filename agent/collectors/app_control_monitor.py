import queue
import threading
import time

from agent.core.policy import get_policy_snapshot


class AppControlMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q
        self.running = False
        self._seen = {}

    def _collect(self):
        policy = get_policy_snapshot()
        entries = policy.get("app_blacklist", []) or []
        if not entries:
            return
        rule_map = {str(item.get("app_name", "")).lower(): str(item.get("action", "kill")).lower() for item in entries}
        now = time.time()

        try:
            import psutil
        except Exception:
            return

        for proc in psutil.process_iter(["pid", "name", "username"]):
            try:
                info = proc.info
                pid = int(info.get("pid"))
                name = str(info.get("name", "")).lower()
                if not name:
                    continue
                matched_key = None
                matched_action = None
                for app_name, action in rule_map.items():
                    if app_name and app_name in name:
                        matched_key = app_name
                        matched_action = action
                        break
                if not matched_key:
                    continue

                last_at = self._seen.get(pid, 0)
                if now - last_at < 20:
                    continue

                killed = False
                if matched_action == "kill":
                    try:
                        proc.kill()
                        killed = True
                    except Exception:
                        killed = False

                self.q.put(
                    {
                        "event_type": "app_blacklist",
                        "severity": "high" if killed else "medium",
                        "payload": {
                            "pid": pid,
                            "process_name": name,
                            "username": str(info.get("username", "")),
                            "blacklist_match": matched_key,
                            "action": matched_action,
                            "killed": killed,
                        },
                    }
                )
                self._seen[pid] = now
            except Exception:
                continue

    def start(self):
        self.running = True

        def loop():
            while self.running:
                self._collect()
                time.sleep(10)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
