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
    "gift card", "wire transfer", "login now", "unusual sign-in"
]

def analyze_process(payload: Dict) -> Dict:
    score, flags = 0, []
    name = str(payload.get("process_name","")).lower()
    cmd = str(payload.get("cmd_line","")).lower()
    for bad in SUSPICIOUS_PROCESSES:
        if bad in name or bad in cmd:
            score += 85; flags.append(f"Malicious process: {bad}"); break
    if "powershell" in name:
        if any(x in cmd for x in ["-enc","-encodedcommand","downloadstring","iex","invoke-expression"]):
            score += 70; flags.append("Encoded/download PowerShell detected")
    if payload.get("elevated") and payload.get("parent","") not in ["services.exe","svchost.exe"]:
        score += 40; flags.append("Unexpected privilege escalation")
    return {"score": min(score,100), "flags": flags}

def analyze_network(payload: Dict) -> Dict:
    score, flags = 0, []
    port = int(payload.get("dest_port",0))
    sent = int(payload.get("bytes_sent",0))
    if port in SUSPICIOUS_PORTS:
        score += 90; flags.append(f"Connection to C2 port {port}")
    if sent > 50_000_000:
        score += 75; flags.append(f"Data exfiltration: {sent//1000000}MB sent")
    if int(payload.get("connection_count",0)) > 50:
        score += 55; flags.append("Network scanning detected")
    if int(payload.get("dns_query_length",0)) > 100:
        score += 60; flags.append("DNS tunneling suspected")
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
    if any(ext in text for ext in [".zip", ".exe", ".html", ".iso", ".scr"]):
        score += 35
        flags.append("Suspicious attachment type referenced")
    if "http://" in text or "bit.ly" in text or "tinyurl" in text:
        score += 30
        flags.append("Shortened or insecure link found")
    if sender and any(dom in sender for dom in [".ru", ".tk", ".xyz", ".top"]):
        score += 25
        flags.append("High-risk sender domain")
    return {"score": min(score, 100), "flags": flags}

def analyze_event(event_type: str, payload: Dict) -> Dict:
    fn = {"process":analyze_process,"network":analyze_network,"login":analyze_login,"file":analyze_file,"email":analyze_email}
    result = fn.get(event_type, lambda p: {"score":0,"flags":[]})(payload)
    result["category"] = event_type
    return result
