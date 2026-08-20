"""
state_manager.py
Persists the last-known signal per pair to a JSON file, so the bot doesn't
re-alert the same signal on every scheduled run.
"""

import json
import os
import config


def load_state() -> dict:
    if not os.path.exists(config.STATE_FILE):
        return {}
    try:
        with open(config.STATE_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        print(f"[STATE WARNING] Could not read state file, starting fresh: {e}")
        return {}


def save_state(state: dict) -> None:
    try:
        with open(config.STATE_FILE, "w") as f:
            json.dump(state, f, indent=2)
    except IOError as e:
        print(f"[STATE ERROR] Could not write state file: {e}")
