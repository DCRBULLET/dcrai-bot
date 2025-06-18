# strategies/doji_confirmation.py

from typing import Optional, Dict
from utils.helpers import pip_size, round_safe

def check_trade_opportunity(chart_data: Dict) -> Optional[Dict]:
    """
    Strategy: Doji Confirmation Breakout
    Detects a doji candle with breakout confirmation.
    Returns standardized trade dictionary.
    """
    candles = chart_data.get("candles", [])
    trend = chart_data.get("trend")
    symbol = chart_data.get("symbol")

    if len(candles) < 3 or not trend or not symbol:
        return None

    try:
        doji = candles[-3]
        confirm = candles[-2]

        body_size = abs(doji["close"] - doji["open"])
        range_size = doji["high"] - doji["low"]
        if range_size == 0 or (body_size / range_size) >= 0.2:
            return None  # Not a valid doji

        # Confirmation: bullish breakout
        if confirm["close"] > doji["high"]:
            pip = pip_size(symbol)
            sl = doji["low"] - (15 * pip)
            tp = confirm["close"] + (confirm["close"] - sl)

            return {
                "symbol": symbol,
                "entry": round_safe(confirm["close"], 3),
                "sl": round_safe(sl, 3),
                "tp": round_safe(tp, 3),
                "strategy": "doji_confirmation",
                "trend": trend,
                "volume_spike": False,
                "confidence": 0
            }

    except (KeyError, IndexError, ZeroDivisionError):
        return None

    return None
