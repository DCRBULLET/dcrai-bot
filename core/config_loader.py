# core/config_loader.py

import json
import os

# Path to config
CONFIG_PATH = os.path.join("config", "config.json")

# Load JSON config
with open(CONFIG_PATH, "r") as f:
    CONFIG = json.load(f)

# Helper accessors (optional)
def get_strategy_map():
    return CONFIG.get("symbol_strategy_map", {})

def get_cooldown_minutes(strategy: str) -> int:
    return CONFIG.get("cooldown_minutes", {}).get(strategy, CONFIG["cooldown_minutes"].get("default", 30))

def get_max_trade_duration() -> int:
    return CONFIG.get("max_trade_duration_minutes", 240)

def get_confidence_threshold(strategy: str) -> int:
    return CONFIG.get("confidence_thresholds", {}).get(strategy, CONFIG["confidence_thresholds"].get("default", 3))

def get_risk_settings():
    return CONFIG.get("risk_management", {})
