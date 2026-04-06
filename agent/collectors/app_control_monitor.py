import queue
import threading
import time

from agent.core.adaptive_guard import is_process_allowlisted, should_enforce_action
from agent.core.config import get_config
from agent.core.policy import get_policy_snapshot


class AppControlMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q
        self.running = False
        self._seen = {}

    def _collect(self):
        cfg = get_config()
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
                if is_process_allowlisted(name, cfg):
                    continue
                matched_key = None
                matched_action = None
                match_score = 0
                for app_name, action in rule_map.items():
                    if not app_name:
                        continue
                    exact = name == app_name or name == f"{app_name}.exe" or app_name == f"{name}.exe"
                    partial = len(app_name) >= 5 and app_name in name
                    if exact or partial:
                        matched_key = app_name
                        matched_action = action
                        match_score = 92 if exact else 78
                        break
                if not matched_key:
                    continue

                last_at = self._seen.get(pid, 0)
                if now - last_at < 20:
                    continue

                killed = False
                enforcement_deferred = False
                if matched_action == "kill":
                    should_kill = should_enforce_action(
                        cfg,
                        action_kind="terminate_process",
                        signal_score=match_score,
                        critical=match_score >= 90,
                    )
                    if should_kill:
                        try:
                            proc.kill()
                            killed = True
                        except Exception:
                            killed = False
                    else:
                        enforcement_deferred = True

                self.q.put(
                    {
                        "event_type": "app_blacklist",
                        "severity": "high" if killed else ("medium" if match_score >= 80 else "low"),
                        "payload": {
                            "pid": pid,
                            "process_name": name,
                            "username": str(info.get("username", "")),
                            "blacklist_match": matched_key,
                            "action": matched_action,
                            "killed": killed,
                            "enforcement_deferred": enforcement_deferred,
                            "detection_score": match_score,
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
