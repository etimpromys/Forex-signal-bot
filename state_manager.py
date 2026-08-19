import json, os
import config

def load_state():
    if not os.path.exists(config.STATE_FILE):
        return {}
    with open(config.STATE_FILE) as f:
        return json.load(f)

def save_state(state):
    with open(config.STATE_FILE, "w") as f:
        json.dump(state, f)
