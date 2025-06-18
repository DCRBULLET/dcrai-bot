# strategies/inversion_fvg.py

from typing import Optional, Dict
from utils.helpers import pip_size, round_safe

def check_trade_opportunity(chart_data: Dict) -> Optional[Dict]:
    """
    Strategy: Inversion Fair Value Gap
    Looks for price breaking back through opposite FVGs.
    Returns standardized trade dictionary.
    """
    candles = chart_data.get("candles", [])
    fair_value_gaps = chart_data.get("fair_value_gaps", [])
    trend = chart_data.get("trend")
    symbol = chart_data.get("symbol")

    if len(candles) < 10 or not fair_value_gaps or not trend or not symbol:
        return None

    try:
        last = candles[-1]
        prior = candles[-2]
        pip = pip_size(symbol)
    except (IndexError, KeyError):
        return None

    # Bullish inversion — broke above bearish FVG
    for fvg in fair_value_gaps:
        price = fvg.get("price")
        if not price or fvg.get("type") != "bearish":
            continue
        if prior["close"] < price < last["close"]:
            swing_high = max(c["high"] for c in candles[-20:])
            return {
                "symbol": symbol,
                "entry": round_safe(last["close"], 3),
                "sl": round_safe(price - 15 * pip, 3),
                "tp": round_safe(swing_high, 3),
                "strategy": "inversion_fvg",
                "trend": trend,
                "volume_spike": False,
                "confidence": 0
            }

    # Bearish inversion — broke below bullish FVG
    for fvg in fair_value_gaps:
        price = fvg.get("price")
        if not price or fvg.get("type") != "bullish":
            continue
        if prior["close"] > price > last["close"]:
            swing_low = min(c["low"] for c in candles[-20:])
            return {
                "symbol": symbol,
                "entry": round_safe(last["close"], 3),
                "sl": round_safe(price + 15 * pip, 3),
                "tp": round_safe(swing_low, 3),
                "strategy": "inversion_fvg",
                "trend": trend,
                "volume_spike": False,
                "confidence": 0
            }

    return None
