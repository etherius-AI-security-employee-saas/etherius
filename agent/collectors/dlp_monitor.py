import os
import queue
import re
import subprocess
import threading
import time


_PATTERNS = {
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "api_key": re.compile(r"(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{16,}", re.IGNORECASE),
}


class DlpMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q
        self.running = False
        self._last_clip = ""
        self._drive_snapshot = {}

    def _get_clipboard_text(self):
        if os.name != "nt":
            return ""
        try:
            result = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                capture_output=True,
                timeout=5,
                text=True,
                encoding="utf-8",
                errors="ignore",
            )
            return (result.stdout or "").strip()
        except Exception:
            return ""

    def _scan_clipboard(self):
        text = self._get_clipboard_text()
        if not text or text == self._last_clip:
            return
        self._last_clip = text
        matched = []
        for name, pattern in _PATTERNS.items():
            try:
                if pattern.search(text):
                    matched.append(name)
            except re.error:
                continue
        if not matched:
            return
        sample = text[:220]
        self.q.put(
            {
                "event_type": "dlp",
                "severity": "high",
                "payload": {
                    "source": "clipboard",
                    "pattern_type": ",".join(matched),
                    "content_sample": sample,
                    "bytes_copied": len(text.encode("utf-8", errors="ignore")),
                    "target": "clipboard",
                },
            }
        )

    def _list_removable_roots(self):
        roots = []
        try:
            import psutil

            for part in psutil.disk_partitions(all=False):
                opts = str(part.opts or "").lower()
                if "removable" in opts:
                    roots.append(part.mountpoint)
        except Exception:
            pass
        return roots

    def _scan_external_copy(self):
        for root in self._list_removable_roots():
            current = {}
            try:
                for name in os.listdir(root):
                    path = os.path.join(root, name)
                    try:
                        stat = os.stat(path)
                        current[path] = (stat.st_mtime, stat.st_size)
                    except Exception:
                        continue
            except Exception:
                continue

            prev = self._drive_snapshot.get(root, {})
            copied_bytes = 0
            for path, (mtime, size) in current.items():
                prev_item = prev.get(path)
                if not prev_item:
                    copied_bytes += size
                elif mtime > prev_item[0] and size > prev_item[1]:
                    copied_bytes += size - prev_item[1]

            if copied_bytes >= 50_000_000:
                self.q.put(
                    {
                        "event_type": "dlp",
                        "severity": "high",
                        "payload": {
                            "source": "file_copy",
                            "pattern_type": "mass_copy",
                            "content_sample": "",
                            "bytes_copied": copied_bytes,
                            "target": "external_drive",
                            "drive": root,
                        },
                    }
                )
            self._drive_snapshot[root] = current

    def _collect(self):
        self._scan_clipboard()
        self._scan_external_copy()

    def start(self):
        self.running = True

        def loop():
            while self.running:
                self._collect()
                time.sleep(30)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
