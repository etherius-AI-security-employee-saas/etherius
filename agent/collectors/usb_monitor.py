import os
import platform
import queue
import shutil
import subprocess
import threading
import time

from agent.core.policy import get_policy_snapshot


class UsbMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q
        self.running = False
        self._known = {}

    def _list_removable(self):
        items = {}
        try:
            import psutil

            for part in psutil.disk_partitions(all=False):
                opts = str(part.opts or "").lower()
                if "removable" not in opts and not str(part.device).lower().startswith(("e:\\", "f:\\", "g:\\", "h:\\")):
                    continue
                mount = part.mountpoint
                size = ""
                try:
                    usage = shutil.disk_usage(mount)
                    size = str(usage.total)
                except Exception:
                    pass
                items[mount] = {
                    "device_id": str(part.device or mount),
                    "device_name": os.path.basename(str(part.device or mount)) or mount,
                    "vendor": "unknown",
                    "size": size,
                }
        except Exception:
            return {}
        return items

    def _safe_eject(self, mountpoint):
        if platform.system() != "Windows":
            return False
        try:
            drive = str(mountpoint).strip()
            if drive.endswith("\\"):
                drive = drive[:-1]
            subprocess.run(
                [
                    "powershell",
                    "-NoProfile",
                    "-Command",
                    f"$d='{drive}'; try {{ (New-Object -ComObject Shell.Application).NameSpace(17).ParseName($d).InvokeVerb('Eject') }} catch {{}}",
                ],
                capture_output=True,
                timeout=8,
            )
            return True
        except Exception:
            return False

    def _collect(self):
        now_items = self._list_removable()
        policy = get_policy_snapshot()
        usb_policy = str(policy.get("usb_policy", "allow_all")).lower()
        whitelist = {str(item).strip().lower() for item in policy.get("usb_whitelist", [])}

        for mount, info in now_items.items():
            if mount not in self._known:
                device_id = str(info.get("device_id", "")).strip()
                should_block = usb_policy == "block_all" or (usb_policy == "whitelist" and device_id.lower() not in whitelist)
                action = "blocked" if should_block else "plugged"
                if should_block:
                    self._safe_eject(mount)
                self.q.put(
                    {
                        "event_type": "usb",
                        "severity": "info",
                        "payload": {
                            "action": action,
                            "device_id": device_id,
                            "device_name": info.get("device_name", ""),
                            "vendor": info.get("vendor", ""),
                            "size": info.get("size", ""),
                            "is_whitelisted": device_id.lower() in whitelist,
                        },
                    }
                )

        for mount, info in self._known.items():
            if mount not in now_items:
                self.q.put(
                    {
                        "event_type": "usb",
                        "severity": "info",
                        "payload": {
                            "action": "removed",
                            "device_id": info.get("device_id", ""),
                            "device_name": info.get("device_name", ""),
                            "vendor": info.get("vendor", ""),
                            "size": info.get("size", ""),
                        },
                    }
                )

        self._known = now_items

    def start(self):
        self.running = True

        def loop():
            while self.running:
                self._collect()
                time.sleep(8)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
