import os
import json

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "shared_paths": [],
    "port": 8000,
    "ngrok_auth_token": "",  # User can provide this for persistent URLs
    "access_password": "",   # Leave empty for no password
}

def load_config():
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "w") as f:
            json.dump(DEFAULT_CONFIG, f, indent=4)
        return DEFAULT_CONFIG
    
    with open(CONFIG_FILE, "r") as f:
        return json.load(f)

def save_config(config):
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=4)

def get_shared_paths():
    config = load_config()
    paths = config.get("shared_paths", [])
    # Always include the local 'shared' folder if it exists
    local_shared = os.path.abspath("shared")
    if not os.path.exists(local_shared):
        os.makedirs(local_shared)
    
    if local_shared not in paths:
        paths.append(local_shared)
    
    return paths
