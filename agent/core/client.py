import requests

from agent.core.config import get_config


def send_heartbeat(timeout=10):
    config = get_config()
    return requests.post(
        f"{config['backend_url']}/api/agent/heartbeat",
        headers={"Authorization": f"Bearer {config['agent_token']}"},
        timeout=timeout,
    )


def send_event(event, timeout=15):
    config = get_config()
    return requests.post(
        f"{config['backend_url']}/api/agent/event",
        json=event,
        headers={"Authorization": f"Bearer {config['agent_token']}"},
        timeout=timeout,
    )


def enroll_device(payload, backend_url, timeout=15):
    return requests.post(
        f"{backend_url}/api/agent/enroll",
        json=payload,
        timeout=timeout,
    )
