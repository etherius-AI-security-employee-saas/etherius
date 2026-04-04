import os
import platform
from datetime import datetime
from pathlib import Path

import psutil


SUSPICIOUS_PROCESS_KEYWORDS = [
    "mimikatz",
    "meterpreter",
    "psexec",
    "cobalt",
    "empire",
    "nc.exe",
    "ncat",
    "procdump",
    "rundll32 -enc",
    "powershell -enc",
]

KNOWN_SAFE_PROCESS_KEYWORDS = [
    "chrome",
    "msedge",
    "teams",
    "zoom",
    "outlook",
    "winword",
    "excel",
    "onenote",
    "slack",
    "code",
    "onedrive",
]

SUSPICIOUS_PORTS = {4444, 5555, 6666, 9001, 9002, 31337, 1337}


def _safe_lower(text):
    return str(text or "").lower()


def _process_scan():
    suspicious = []
    safe_hits = 0
    total = 0

    for proc in psutil.process_iter(attrs=["pid", "name", "cmdline", "username"]):
        total += 1
        try:
            name = _safe_lower(proc.info.get("name"))
            cmd = " ".join(proc.info.get("cmdline") or [])
            cmd_lower = _safe_lower(cmd)
            normalized = f"{name} {cmd_lower}"

            if any(safe in normalized for safe in KNOWN_SAFE_PROCESS_KEYWORDS):
                safe_hits += 1
                continue

            for marker in SUSPICIOUS_PROCESS_KEYWORDS:
                if marker in normalized:
                    suspicious.append(
                        {
                            "pid": proc.info.get("pid"),
                            "name": proc.info.get("name"),
                            "cmdline": cmd[:220],
                            "reason": f"Matched suspicious marker: {marker}",
                        }
                    )
                    break
        except Exception:
            continue

    return {"total": total, "safe_hits": safe_hits, "suspicious": suspicious}


def _network_scan():
    suspicious = []
    total = 0
    try:
        for conn in psutil.net_connections(kind="inet"):
            total += 1
            laddr = getattr(conn, "laddr", None)
            raddr = getattr(conn, "raddr", None)
            if not raddr:
                continue
            remote_port = getattr(raddr, "port", None)
            if remote_port in SUSPICIOUS_PORTS:
                suspicious.append(
                    {
                        "local": f"{getattr(laddr, 'ip', '')}:{getattr(laddr, 'port', '')}",
                        "remote": f"{getattr(raddr, 'ip', '')}:{getattr(raddr, 'port', '')}",
                        "status": conn.status,
                        "reason": "Connection to suspicious C2-like port",
                    }
                )
    except Exception:
        pass
    return {"total": total, "suspicious": suspicious}


def _filesystem_scan():
    findings = []
    candidate_paths = []
    if platform.system().lower() == "windows":
        appdata = os.environ.get("APPDATA", "")
        local = os.environ.get("LOCALAPPDATA", "")
        startup_1 = Path(appdata) / "Microsoft/Windows/Start Menu/Programs/Startup" if appdata else None
        startup_2 = Path(local) / "Temp" if local else None
        for path in [startup_1, startup_2]:
            if path and path.exists():
                candidate_paths.append(path)

    suspicious_ext = {".vbs", ".js", ".hta", ".bat", ".cmd", ".ps1", ".scr", ".exe"}
    for base in candidate_paths:
        try:
            for item in base.glob("*"):
                if not item.is_file():
                    continue
                if item.suffix.lower() in suspicious_ext:
                    findings.append(
                        {
                            "path": str(item),
                            "size": item.stat().st_size,
                            "reason": "Suspicious executable/script file in sensitive user path",
                        }
                    )
        except Exception:
            continue
    return {"findings": findings}


def run_threat_scan(deep=False):
    process_info = _process_scan()
    network_info = _network_scan()
    fs_info = _filesystem_scan() if deep else {"findings": []}

    suspicious_count = (
        len(process_info["suspicious"]) + len(network_info["suspicious"]) + len(fs_info["findings"])
    )
    score = min(20 + suspicious_count * (18 if deep else 14), 100)
    severity = "critical" if score >= 85 else "high" if score >= 65 else "medium" if score >= 40 else "low"

    findings = {
        "process_hits": process_info["suspicious"][:20],
        "network_hits": network_info["suspicious"][:20],
        "filesystem_hits": fs_info["findings"][:20],
    }
    summary = {
        "mode": "deep" if deep else "quick",
        "scan_timestamp": datetime.utcnow().isoformat(),
        "host_platform": platform.platform(),
        "processes_checked": process_info["total"],
        "network_connections_checked": network_info["total"],
        "safe_process_allowlist_hits": process_info["safe_hits"],
        "suspicious_items_found": suspicious_count,
        "local_scan_risk_score": score,
        "local_scan_severity": severity,
        "advisory_mode_only": True,
    }
    return {"summary": summary, "findings": findings}
