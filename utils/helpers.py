# utils/helpers.py

import uuid
from datetime import datetime
import pytz


def pip_size(symbol: str) -> float:
    """
    Returns pip size based on the symbol.
    """
    if symbol == "XAUUSD":
        return 0.1
    elif symbol.endswith("JPY"):
        return 0.01
    else:
        return 0.0001


def generate_trade_id() -> str:
    """
    Generates a unique ID for every trade.
    """
    return str(uuid.uuid4())[:8]  # short and clean


def now_utc() -> str:
    """
    Returns current time in UTC.
    """
    return datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')


def now_ist() -> str:
    """
    Returns current time in IST (for logging).
    """
    ist = pytz.timezone("Asia/Kolkata")
    return datetime.now(ist).strftime('%Y-%m-%d %H:%M:%S')


def normalize_symbol(symbol: str) -> str:
    """
    Normalize symbol format to maintain broker compatibility.
    """
    return symbol.strip()  # ⬅️ Don't change case


def round_safe(value: float, digits: int = 2) -> float:
    """
    Rounds a float safely.
    """
    try:
        return round(float(value), digits)
    except:
        return 0.0
