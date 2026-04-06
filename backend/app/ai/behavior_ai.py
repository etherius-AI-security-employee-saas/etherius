from typing import Dict, Any

SUSPICIOUS_PROCESSES = [
    "mimikatz","netcat","nc.exe","nmap","psexec","meterpreter",
    "cobalt","empire","bloodhound","lazagne","procdump","pwdump",
    "wce","vssadmin","bcdedit","reg.exe"
]
SUSPICIOUS_PORTS = [4444,5555,1337,31337,6666,9001,9002,8888]
SENSITIVE_PATHS = [
    "c:\\windows\\system32\\lsass","c:\\sam","c:\\windows\\ntds",
    "/etc/shadow","/etc/passwd","/root/.ssh"
]
SUSPICIOUS_EMAIL_KEYWORDS = [
    "urgent", "verify account", "password reset", "invoice attached",
    "gift card", "wire transfer", "login now", "unusual sign-in",
    "mfa expired", "confirm payroll", "document shared", "security alert"
]
SENSITIVE_DLP_PATTERNS = [
    ("ssn", r"\b\d{3}-\d{2}-\d{4}\b"),
    ("credit_card", r"\b(?:\d[ -]*?){13,16}\b"),
    ("api_key", r"(api[_-]?key|secret|token)\s*[:=]\s*[A-Za-z0-9_\-]{16,}"),
]

def analyze_process(payload: Dict) -> Dict:
    score, flags = 0, []
    name = str(payload.get("process_name","")).lower()
    cmd = str(payload.get("cmd_line","")).lower()
    action = str(payload.get("action", "")).lower()
    for bad in SUSPICIOUS_PROCESSES:
        if bad in name or bad in cmd:
            score += 85; flags.append(f"Malicious process: {bad}"); break
    if "powershell" in name:
        if any(x in cmd for x in ["-enc","-encodedcommand","downloadstring","iex","invoke-expression"]):
            score += 70; flags.append("Encoded/download PowerShell detected")
    if action == "exploit_chain_blocked":
        score += 90; flags.append("Office/browser exploit chain blocked")
    elif action == "exploit_chain_detected":
        score += 72; flags.append("Office/browser exploit chain detected")
    if payload.get("elevated") and payload.get("parent","") not in ["services.exe","svchost.exe"]:
        score += 40; flags.append("Unexpected privilege escalation")
    return {"score": min(score,100), "flags": flags}

def analyze_network(payload: Dict) -> Dict:
    score, flags = 0, []
    port = int(payload.get("dest_port",0))
    sent = int(payload.get("bytes_sent",0))
    action = str(payload.get("action", "")).lower()
    if port in SUSPICIOUS_PORTS:
        score += 90; flags.append(f"Connection to C2 port {port}")
    if sent > 50_000_000:
        score += 75; flags.append(f"Data exfiltration: {sent//1000000}MB sent")
    if int(payload.get("connection_count",0)) > 50:
        score += 55; flags.append("Network scanning detected")
    if int(payload.get("dns_query_length",0)) > 100:
        score += 60; flags.append("DNS tunneling suspected")
    if action == "beacon_pattern_detected":
        score += 70; flags.append("Beaconing/exfiltration pattern detected")
        if bool(payload.get("local_blocked", False)):
            score += 15; flags.append("Outbound beacon IP locally blocked")
    return {"score": min(score,100), "flags": flags}

def analyze_login(payload: Dict) -> Dict:
    score, flags = 0, []
    fails = int(payload.get("failed_attempts",0))
    hour = int(payload.get("hour_of_day",12))
    if fails >= 5: score += 75; flags.append(f"Brute force: {fails} failures")
    elif fails >= 3: score += 35; flags.append(f"Multiple login failures: {fails}")
    if hour < 6 or hour > 22: score += 30; flags.append(f"After-hours access at {hour}:00")
    if payload.get("new_location"): score += 40; flags.append("Login from new location")
    return {"score": min(score,100), "flags": flags}

def analyze_file(payload: Dict) -> Dict:
    score, flags = 0, []
    path = str(payload.get("file_path","")).lower()
    action = str(payload.get("action","")).lower()
    count = int(payload.get("files_affected",1))
    for sp in SENSITIVE_PATHS:
        if sp in path: score += 65; flags.append(f"Sensitive path access: {sp}"); break
    if count > 100 and action in ["modify","delete","encrypt"]:
        score += 95; flags.append(f"RANSOMWARE INDICATOR: {count} files {action}d")
    if path.endswith((".exe",".bat",".ps1",".vbs")) and action == "create":
        score += 55; flags.append(f"Executable file created: {path}")
    if action == "quarantine":
        score += 82; flags.append("Suspicious download quarantined before execution")
    elif action == "suspicious_download_detected":
        score += 60; flags.append("Suspicious download detected in user space")
    reason = str(payload.get("reason", "")).lower()
    if reason and "double-extension" in reason:
        score += 20; flags.append("Masquerading double-extension file pattern")
    return {"score": min(score,100), "flags": flags}

def analyze_email(payload: Dict) -> Dict:
    score, flags = 0, []
    subject = str(payload.get("subject", "")).lower()
    body = str(payload.get("body", "")).lower()
    sender = str(payload.get("sender", "")).lower()
    text = f"{subject} {body}"
    keyword_hits = [word for word in SUSPICIOUS_EMAIL_KEYWORDS if word in text]
    if keyword_hits:
        score += min(20 * len(keyword_hits), 60)
        flags.append("Phishing language indicators detected")
    if any(ext in text for ext in [".zip", ".exe", ".html", ".iso", ".scr", ".js", ".vbs", ".hta", ".lnk"]):
        score += 35
        flags.append("Suspicious attachment type referenced")
    if any(token in text for token in ["enable content", "enable macros", "macro", "password protected"]):
        score += 20
        flags.append("Potential malicious document lure")
    if "http://" in text or "bit.ly" in text or "tinyurl" in text:
        score += 30
        flags.append("Shortened or insecure link found")
    if sender and any(dom in sender for dom in [".ru", ".tk", ".xyz", ".top"]):
        score += 25
        flags.append("High-risk sender domain")
    return {"score": min(score, 100), "flags": flags}


def analyze_threat_scan(payload: Dict) -> Dict:
    score, flags = 0, []
    suspicious = int(payload.get("suspicious_items_found", 0) or 0)
    allowlisted = int(payload.get("safe_process_allowlist_hits", 0) or 0)
    mode = str(payload.get("mode", "quick")).lower()

    if suspicious >= 8:
        score += 90
        flags.append(f"High-volume suspicious artifacts in {mode} scan")
    elif suspicious >= 4:
        score += 70
        flags.append(f"Multiple suspicious artifacts in {mode} scan")
    elif suspicious >= 1:
        score += 45
        flags.append(f"Suspicious artifact identified in {mode} scan")
    else:
        score += 15
        flags.append("No high-confidence malicious artifacts found")

    if allowlisted >= 25:
        score = max(score - 10, 0)
        flags.append("Business-safe process allowlist applied")

    if bool(payload.get("advisory_mode_only", False)):
        flags.append("Advisory mode active (no automatic blocking)")

    return {"score": min(score, 100), "flags": flags}


def analyze_usb(payload: Dict) -> Dict:
    score, flags = 0, []
    device_id = str(payload.get("device_id", "")).strip()
    known = bool(payload.get("is_whitelisted", False))
    action = str(payload.get("action", "")).lower()
    if action == "plugged" and not known:
        score += 75
        flags.append("Unknown USB device inserted")
    if action == "blocked":
        score += 85
        flags.append("USB blocked by policy")
    if action == "removed":
        score += 5
    if str(payload.get("vendor", "")).strip().lower() in {"", "unknown"} and action in {"plugged", "blocked"}:
        score += 10
        flags.append("USB vendor identity unavailable")
    if device_id and any(tag in device_id.lower() for tag in ["vid_", "pid_"]):
        score += 10
    return {"score": min(score, 100), "flags": flags}


def analyze_dlp(payload: Dict) -> Dict:
    import re

    score, flags = 0, []
    content = str(payload.get("content_sample", "")).lower()
    bytes_copied = int(payload.get("bytes_copied", 0) or 0)
    pattern_type = str(payload.get("pattern_type", "")).strip().lower()
    explicit_matches = int(payload.get("matches", 0) or 0)
    if bytes_copied > 100_000_000:
        score += 80
        flags.append("Mass copy to external media/cloud")
    elif bytes_copied > 25_000_000:
        score += 50
        flags.append("Large data transfer detected")

    matched = []
    for name, pattern in SENSITIVE_DLP_PATTERNS:
        try:
            if re.search(pattern, content, flags=re.IGNORECASE):
                matched.append(name)
        except re.error:
            continue
    if pattern_type:
        for item in [x.strip() for x in pattern_type.split(",") if x.strip()]:
            if item not in matched:
                matched.append(item)
    if matched:
        score += min(20 * len(matched), 60)
        flags.append(f"Sensitive pattern(s) detected: {', '.join(matched)}")
    if explicit_matches > 0:
        score += min(explicit_matches * 8, 35)
        flags.append(f"Sensitive data match count elevated: {explicit_matches}")

    if str(payload.get("target", "")).lower() in {"dropbox", "gdrive", "googledrive", "onedrive-personal"}:
        score += 25
        flags.append("Upload to external cloud storage")
    if str(payload.get("target", "")).lower() in {"external_drive", "usb", "removable_media"}:
        score += 20
        flags.append("Sensitive copy to removable media")

    return {"score": min(score, 100), "flags": flags}


def analyze_web(payload: Dict) -> Dict:
    score, flags = 0, []
    domain = str(payload.get("domain", "")).lower()
    blocked = bool(payload.get("blocked", False))
    category = str(payload.get("category", "custom")).lower()
    if blocked:
        score += 55
        flags.append(f"Blocked website access attempt: {domain}")
    if category in {"adult", "gambling"}:
        score += 25
        flags.append(f"Policy-sensitive category visited: {category}")
    if category == "social":
        score += 10
    return {"score": min(score, 100), "flags": flags}


def analyze_vulnerability(payload: Dict) -> Dict:
    score, flags = 0, []
    critical = int(payload.get("critical_count", 0) or 0)
    high = int(payload.get("high_count", 0) or 0)
    if critical > 0:
        score += min(critical * 20, 80)
        flags.append(f"Critical vulnerabilities found: {critical}")
    if high > 0:
        score += min(high * 10, 40)
        flags.append(f"High vulnerabilities found: {high}")
    return {"score": min(score, 100), "flags": flags}


def analyze_app_blacklist(payload: Dict) -> Dict:
    score, flags = 0, []
    app_name = str(payload.get("process_name", "")).strip().lower()
    blacklist_match = str(payload.get("blacklist_match", app_name)).strip().lower()
    action = str(payload.get("action", "alert")).strip().lower()
    killed = bool(payload.get("killed", False))
    username = str(payload.get("username", "")).strip()

    if action == "kill" and killed:
        score += 92
        flags.append(f"Blacklisted application terminated: {blacklist_match or app_name}")
    elif action == "kill":
        score += 72
        flags.append(f"Blacklisted application detected (termination pending/failed): {blacklist_match or app_name}")
    else:
        score += 58
        flags.append(f"Blacklisted application detected: {blacklist_match or app_name}")

    if username:
        flags.append(f"Execution attempted by user: {username}")
    return {"score": min(score, 100), "flags": flags}

def analyze_event(event_type: str, payload: Dict) -> Dict:
    fn = {
        "process": analyze_process,
        "network": analyze_network,
        "login": analyze_login,
        "session_heartbeat": analyze_login,
        "employee_login": analyze_login,
        "employee_logout": analyze_login,
        "file": analyze_file,
        "email": analyze_email,
        "threat_scan": analyze_threat_scan,
        "usb": analyze_usb,
        "dlp": analyze_dlp,
        "web": analyze_web,
        "vulnerability": analyze_vulnerability,
        "app_blacklist": analyze_app_blacklist,
    }
    result = fn.get(event_type, lambda p: {"score":0,"flags":[]})(payload)
    result["category"] = event_type
    return result
