import hashlib
import os
import platform
import queue
import shutil
import threading
import time
from pathlib import Path

from agent.core.config import get_config


SUSPICIOUS_EXTENSIONS = {
    ".exe",
    ".dll",
    ".scr",
    ".js",
    ".jse",
    ".vbs",
    ".vbe",
    ".ps1",
    ".bat",
    ".cmd",
    ".hta",
    ".lnk",
    ".iso",
}

DOC_EXTENSIONS = {".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".png", ".jpg", ".jpeg"}
SUSPICIOUS_NAME_TOKENS = {
    "invoice",
    "payment",
    "urgent",
    "password",
    "payroll",
    "salary",
    "security",
    "patch",
    "statement",
    "bank",
    "wire",
    "offer",
    "resume",
}


def _safe_bool(value, default=False):
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class DownloadShieldMonitor:
    def __init__(self, q: queue.Queue):
        self.q = q
        self.running = False
        self._snapshot = {}
        self._seen = set()

    def _watch_roots(self):
        home = Path.home()
        roots = []
        for child in ["Downloads", "Desktop", "Documents"]:
            p = home / child
            if p.exists():
                roots.append(p)
        return roots

    def _hash_file(self, path: Path):
        digest = hashlib.sha256()
        with path.open("rb") as fp:
            for chunk in iter(lambda: fp.read(1024 * 1024), b""):
                digest.update(chunk)
        return digest.hexdigest()

    def _is_suspicious_download(self, path: Path):
        name = path.name.lower()
        suffixes = [s.lower() for s in path.suffixes]
        final_ext = suffixes[-1] if suffixes else ""
        if final_ext in SUSPICIOUS_EXTENSIONS:
            return True, f"High-risk executable/script extension detected ({final_ext})"

        if len(suffixes) >= 2:
            first = suffixes[-2]
            second = suffixes[-1]
            if first in DOC_EXTENSIONS and second in SUSPICIOUS_EXTENSIONS:
                return True, "Double-extension masquerading file detected"

        if final_ext in {".zip", ".rar", ".7z"} and any(token in name for token in SUSPICIOUS_NAME_TOKENS):
            return True, "Suspicious archive naming pattern detected"

        return False, ""

    def _quarantine_dir(self):
        if os.name == "nt":
            base = Path(os.environ.get("PROGRAMDATA", str(Path.home())))
            return base / "Etherius" / "Quarantine"
        return Path.home() / ".etherius" / "quarantine"

    def _quarantine(self, path: Path):
        qdir = self._quarantine_dir()
        qdir.mkdir(parents=True, exist_ok=True)
        target = qdir / f"{int(time.time())}_{path.name}"
        shutil.move(str(path), str(target))
        return target

    def _collect_root(self, root: Path):
        previous = self._snapshot.get(str(root), {})
        current = {}
        try:
            for item in root.iterdir():
                if not item.is_file():
                    continue
                try:
                    st = item.stat()
                except Exception:
                    continue
                current[str(item)] = (st.st_mtime, st.st_size)
        except Exception:
            self._snapshot[str(root)] = current
            return

        cfg = get_config()
        enabled = _safe_bool(cfg.get("download_shield_enabled", True), True)
        if not enabled:
            self._snapshot[str(root)] = current
            return

        policy_mode = str(cfg.get("policy_mode", "advisory")).strip().lower()
        quarantine_enabled = _safe_bool(cfg.get("download_shield_quarantine", True), True)

        for path_text, meta in current.items():
            if path_text in previous and previous[path_text] == meta:
                continue
            key = f"{path_text}:{meta[0]}"
            if key in self._seen:
                continue
            self._seen.add(key)

            file_path = Path(path_text)
            suspicious, reason = self._is_suspicious_download(file_path)
            if not suspicious:
                continue

            sha256 = ""
            try:
                sha256 = self._hash_file(file_path)
            except Exception:
                sha256 = ""

            quarantined = False
            quarantine_path = ""
            action = "suspicious_download_detected"
            if quarantine_enabled and policy_mode in {"balanced", "strict"}:
                try:
                    moved = self._quarantine(file_path)
                    quarantined = True
                    quarantine_path = str(moved)
                    action = "quarantine"
                except Exception:
                    quarantined = False

            self.q.put(
                {
                    "event_type": "file",
                    "severity": "high" if quarantined else "medium",
                    "payload": {
                        "directory": str(root),
                        "action": action,
                        "files_affected": 1,
                        "file_path": str(file_path),
                        "platform": platform.system(),
                        "reason": reason,
                        "sha256": sha256,
                        "file_size": int(meta[1]),
                        "quarantined": quarantined,
                        "quarantine_path": quarantine_path,
                    },
                }
            )

        self._snapshot[str(root)] = current
        if len(self._seen) > 6000:
            self._seen = set(list(self._seen)[-3000:])

    def _collect(self):
        for root in self._watch_roots():
            self._collect_root(root)

    def start(self):
        self.running = True

        def loop():
            while self.running:
                self._collect()
                time.sleep(20)

        threading.Thread(target=loop, daemon=True).start()

    def stop(self):
        self.running = False
