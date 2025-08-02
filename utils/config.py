import json
import os
from datetime import datetime

CONFIG_FOLDER = os.path.expanduser("~/.config/EVE-L_Preview")
os.makedirs(CONFIG_FOLDER, exist_ok=True)
CONFIG_FILE = os.path.join(CONFIG_FOLDER, "EVE-L_Preview.json")
REFRESH_RATE = 1000

DEFAULT_CONFIG = {
    "metadata": {
        "lastmodified": str(datetime.now())
    },
    "settings": {
        "thumbnail_scaling": 5.0,
        "thumbnail_opacity": 100,
        "application_position": [100, 100],
        "enable_borders": True,
        "active_border_color": "#47f73e",
        "inactive_border_color": "#808080",
        "font_family": "Courier New"
    },
    "thumbnail_position": {},
    "hotkeys": {
        "character_list": {}
    }
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r') as f:
                config = json.load(f)
                # Ensure all required keys exist for backward compatibility
                if "hotkeys" not in config:
                    config["hotkeys"] = {"character_list": {}}
                if "character_list" not in config.get("hotkeys", {}):
                    config["hotkeys"]["character_list"] = {}
                return config
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not load config file {CONFIG_FILE}: {e}")
            print("Using default configuration.")
    return DEFAULT_CONFIG

def save_config(config):
    config["metadata"]["lastmodified"] = str(datetime.now())
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)