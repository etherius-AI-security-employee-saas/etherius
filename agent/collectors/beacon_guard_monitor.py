import ipaddress
import os
import platform
import queue
import subprocess
import threading
import time
from collections import defaultdict, deque

from agent.core.config import get_config


def _safe_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _is_public_ip(ip_text: str):
    try:
        ip = ipaddress.ip_address(ip_text)
    except ValueError:
        return False
    return not (ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_multicast or ip.is_reserved)


class BeaconGuardMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q
        self.running = False
        self._ip_hits = defaultdict(deque)
        self._alerted_until = {}

    def _block_ip_locally(self, ip_text: str):
        if os.name != "nt":
            return False
        rule_name = f"EtheriusBeaconBlock_{ip_text.replace('.', '_')}"
        try:
            subprocess.run(
                [
                    "netsh",
                    "advfirewall",
                    "firewall",
                    "add",
                    "rule",
                    f"name={rule_name}",
                    "dir=out",
                    "action=block",
                    f"remoteip={ip_text}",
                    "enable=yes",
                ],
                capture_output=True,
                timeout=8,
            )
            return True
        except Exception:
            return False

    def _collect(self):
        cfg = get_config()
        if not _safe_bool(cfg.get("beacon_guard_enabled", True), True):
            return

        policy_mode = str(cfg.get("policy_mode", "advisory")).strip().lower()
        block_on_detect = _safe_bool(cfg.get("beacon_guard_block", False), False) and policy_mode == "strict"
        now = time.time()

        try:
            import psutil
        except Exception:
            return

        ip_counter = defaultdict(int)
        port_counter = defaultdict(int)
        try:
            connections = psutil.net_connections(kind="inet")
        except Exception:
            connections = []

        for conn in connections:
            try:
                if conn.status != "ESTABLISHED" or not conn.raddr:
                    continue
                dest_ip = str(conn.raddr.ip)
                if not _is_public_ip(dest_ip):
                    continue
                dest_port = int(conn.raddr.port or 0)
                ip_counter[dest_ip] += 1
                port_counter[(dest_ip, dest_port)] += 1
            except Exception:
                continue

        for dest_ip, count in ip_counter.items():
            hits = self._ip_hits[dest_ip]
            hits.append(now)
            while hits and hits[0] < now - 90:
                hits.popleft()

            window_count = len(hits) + count
            if window_count < 14:
                continue

            alert_until = self._alerted_until.get(dest_ip, 0)
            if now < alert_until:
                continue
            self._alerted_until[dest_ip] = now + 300

            top_port = 0
            top_port_count = 0
            for (ip, port), pc in port_counter.items():
                if ip == dest_ip and pc > top_port_count:
                    top_port = port
                    top_port_count = pc

            local_blocked = False
            if block_on_detect:
                local_blocked = self._block_ip_locally(dest_ip)

            io = psutil.net_io_counters()
            self.q.put(
                {
                    "event_type": "network",
                    "severity": "high",
                    "payload": {
                        "dest_ip": dest_ip,
                        "dest_port": top_port,
                        "connection_count": window_count,
                        "bytes_sent": int(getattr(io, "bytes_sent", 0) or 0),
                        "bytes_recv": int(getattr(io, "bytes_recv", 0) or 0),
                        "action": "beacon_pattern_detected",
                        "local_blocked": local_blocked,
                        "platform": platform.system(),
                    },
                }
            )

        # Cleanup stale state.
        stale = [ip for ip, until in self._alerted_until.items() if now - until > 1800]
        for ip in stale:
            self._alerted_until.pop(ip, None)
            self._ip_hits.pop(ip, None)

    def start(self):
        self.running = True

        def loop():
            while self.running:
                self._collect()
                time.sleep(15)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
