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


def get_policies(timeout=15):
    config = get_config()
    return requests.get(
        f"{config['backend_url']}/api/agent/policies",
        headers={"Authorization": f"Bearer {config['agent_token']}"},
        timeout=timeout,
    )


def get_commands(timeout=15):
    config = get_config()
    return requests.get(
        f"{config['backend_url']}/api/agent/commands",
        headers={"Authorization": f"Bearer {config['agent_token']}"},
        timeout=timeout,
    )


def send_command_result(command_id, status, result_text="", timeout=15):
    config = get_config()
    return requests.post(
        f"{config['backend_url']}/api/agent/commands/{command_id}/result",
        json={"status": status, "result_text": result_text},
        headers={"Authorization": f"Bearer {config['agent_token']}"},
        timeout=timeout,
    )


def send_software_inventory(items, timeout=30):
    config = get_config()
    return requests.post(
        f"{config['backend_url']}/api/agent/software-inventory",
        json={"items": items},
        headers={"Authorization": f"Bearer {config['agent_token']}"},
        timeout=timeout,
    )


def enroll_device(payload, backend_url, timeout=15):
    return requests.post(
        f"{backend_url}/api/agent/enroll",
        json=payload,
        timeout=timeout,
    )
