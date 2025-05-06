import json
import os
from datetime import datetime

CONFIG_FILE = "EVE-L_Preview.json"


BASE_REFRESH_RATE = 500
BASE_CLIENT_COUNT = 2
RATE_PER_CLIENT = 250

def calculate_refresh_rate(client_count):
    """Calculate refresh rate based on number of clients"""
    if (client_count <= BASE_CLIENT_COUNT):
        return BASE_REFRESH_RATE
    else:
        return BASE_REFRESH_RATE + (client_count - BASE_CLIENT_COUNT) * RATE_PER_CLIENT

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
        "font_family": "Courier New",
        "dynamic_refresh": True  # Add option to toggle dynamic refresh
    },
    "thumbnail_position": {}
}

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            return json.load(f)
    return DEFAULT_CONFIG

def save_config(config):
    config["metadata"]["lastmodified"] = str(datetime.now())
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=4)