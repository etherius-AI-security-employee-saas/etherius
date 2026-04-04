import json
import os

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'agent_config.json')

def load_config():
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(cfg):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(cfg, f, indent=2)

config = load_config()


def get_config():
    global config
    config = load_config()
    return config


def update_config(partial):
    current = get_config()
    current.update(partial)
    save_config(current)
    return get_config()
