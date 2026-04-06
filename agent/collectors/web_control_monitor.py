import os
import queue
import shutil
import sqlite3
import tempfile
import threading
import time
from datetime import datetime, timedelta

from agent.core.adaptive_guard import is_domain_allowlisted, should_enforce_action
from agent.core.config import get_config
from agent.core.policy import get_policy_snapshot


def _safe_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class WebControlMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q
        self.running = False
        self._seen_urls = set()
        self._hosts_applied = ""

    def _hosts_file(self):
        if os.name == "nt":
            return r"C:\Windows\System32\drivers\etc\hosts"
        return "/etc/hosts"

    def _apply_hosts_block(self, blocked_domains):
        marker_start = "# Etherius managed block list start"
        marker_end = "# Etherius managed block list end"
        payload = [marker_start]
        for item in blocked_domains:
            domain = str(item.get("domain", "")).strip().lower()
            if not domain:
                continue
            payload.append(f"127.0.0.1 {domain}")
            payload.append(f"127.0.0.1 www.{domain}")
        payload.append(marker_end)
        block_text = "\n".join(payload)
        if block_text == self._hosts_applied:
            return

        hosts_path = self._hosts_file()
        try:
            with open(hosts_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
        except Exception:
            return

        start_idx = content.find(marker_start)
        end_idx = content.find(marker_end)
        if start_idx >= 0 and end_idx > start_idx:
            end_idx += len(marker_end)
            updated = content[:start_idx].rstrip() + "\n\n" + block_text + "\n" + content[end_idx:].lstrip("\n")
        else:
            updated = content.rstrip() + "\n\n" + block_text + "\n"

        try:
            with open(hosts_path, "w", encoding="utf-8") as f:
                f.write(updated)
            self._hosts_applied = block_text
        except Exception:
            pass

    def _history_sources(self):
        local = os.environ.get("LOCALAPPDATA", "")
        return [
            os.path.join(local, "Google", "Chrome", "User Data", "Default", "History"),
            os.path.join(local, "Microsoft", "Edge", "User Data", "Default", "History"),
        ]

    def _extract_recent_urls(self):
        rows = []
        threshold = datetime.utcnow() - timedelta(minutes=15)
        chrome_epoch = datetime(1601, 1, 1)
        for src in self._history_sources():
            if not os.path.exists(src):
                continue
            tmp = None
            try:
                fd, tmp = tempfile.mkstemp(suffix=".sqlite")
                os.close(fd)
                shutil.copy2(src, tmp)
                conn = sqlite3.connect(tmp)
                cur = conn.cursor()
                cur.execute("SELECT url, last_visit_time FROM urls ORDER BY last_visit_time DESC LIMIT 200")
                for url, last_visit_time in cur.fetchall():
                    try:
                        ts = chrome_epoch + timedelta(microseconds=int(last_visit_time))
                    except Exception:
                        ts = None
                    if ts and ts >= threshold:
                        rows.append((str(url or ""), ts))
                conn.close()
            except Exception:
                pass
            finally:
                if tmp and os.path.exists(tmp):
                    try:
                        os.remove(tmp)
                    except Exception:
                        pass
        return rows

    def _collect(self):
        cfg = get_config()
        policy_mode = str(cfg.get("policy_mode", "advisory")).strip().lower()
        web_enforce = _safe_bool(cfg.get("web_control_enforce", False), False)
        non_disruptive_mode = _safe_bool(cfg.get("non_disruptive_mode", True), True)

        policy = get_policy_snapshot()
        blocked_domains = policy.get("blocked_domains", []) or []
        should_apply_hosts = web_enforce and policy_mode == "strict" and not non_disruptive_mode
        self._apply_hosts_block(blocked_domains if should_apply_hosts else [])
        if not blocked_domains:
            return
        recent_urls = self._extract_recent_urls()
        for url, ts in recent_urls:
            key = f"{url}|{ts.isoformat()}"
            if key in self._seen_urls:
                continue
            matched = None
            for item in blocked_domains:
                domain = str(item.get("domain", "")).strip().lower()
                if domain and domain in url.lower():
                    matched = item
                    break
            if not matched:
                continue
            domain = str(matched.get("domain", "")).strip().lower()
            if is_domain_allowlisted(domain, cfg):
                continue

            category = str(matched.get("category", "custom")).strip().lower()
            signal_score = 72 if category in {"adult", "gambling", "malware", "phishing"} else 58
            blocked = should_apply_hosts and should_enforce_action(
                cfg,
                action_kind="hosts_block",
                signal_score=signal_score,
                critical=category in {"malware", "phishing"},
            )
            action = "blocked" if blocked else "policy_violation_detected"
            self.q.put(
                {
                    "event_type": "web",
                    "severity": "medium" if blocked else "low",
                    "payload": {
                        "url": url,
                        "domain": domain,
                        "category": category or "custom",
                        "blocked": blocked,
                        "action": action,
                        "detection_score": signal_score,
                        "enforcement_deferred": bool(web_enforce and not blocked),
                        "visited_at": ts.isoformat(),
                    },
                }
            )
            self._seen_urls.add(key)
            if len(self._seen_urls) > 4000:
                self._seen_urls = set(list(self._seen_urls)[-2000:])

    def start(self):
        self.running = True

        def loop():
            while self.running:
                self._collect()
                time.sleep(45)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
