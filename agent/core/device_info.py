import getpass
import os
import platform
import socket
import uuid


def get_mac_address():
    mac = uuid.getnode()
    return ":".join(f"{(mac >> ele) & 0xff:02X}" for ele in range(40, -1, -8))


def get_ip_address():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.connect(("8.8.8.8", 80))
            return sock.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


def collect_device_info():
    return {
        "hostname": socket.gethostname(),
        "os": f"{platform.system()} {platform.release()}".strip(),
        "ip_address": get_ip_address(),
        "mac_address": get_mac_address(),
        "agent_version": "1.1.0",
        "device_user": getpass.getuser(),
    }
