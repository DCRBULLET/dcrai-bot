# strategies/volume_liquidity.py

from typing import Optional, Dict
from utils.helpers import pip_size, round_safe

def check_trade_opportunity(chart_data: Dict) -> Optional[Dict]:
    """
    Strategy: Volume Liquidity Trap
    Detects a price drop on below-average volume near bullish FVG.
    Returns standardized trade dictionary.
    """
    candles = chart_data.get("candles", [])
    volumes = chart_data.get("volume_series", [])
    fair_value_gaps = chart_data.get("fair_value_gaps", [])
    trend = chart_data.get("trend")
    symbol = chart_data.get("symbol")

    if len(candles) < 20 or len(volumes) < 20 or not fair_value_gaps or not symbol:
        return None

    pip = pip_size(symbol)

    try:
        recent_volume = volumes[-1]
        avg_volume = sum(volumes[-11:-1]) / 10
        price_dropped = (
            candles[-2]["close"] < candles[-2]["open"] and
            candles[-1]["close"] < candles[-2]["close"]
        )
        flat_volume = 0 < recent_volume < avg_volume * 0.9

        if price_dropped and flat_volume:
            for fvg in fair_value_gaps:
                if fvg.get("type") != "bullish":
                    continue

                entry = fvg.get("price")
                if entry is None:
                    continue

                stop_loss = entry - 5 * pip
                take_profit = max(candle["high"] for candle in candles[-20:])

                return {
                    "symbol": symbol,
                    "entry": round_safe(entry, 3),
                    "sl": round_safe(stop_loss, 3),
                    "tp": round_safe(take_profit, 3),
                    "strategy": "volume_liquidity",
                    "trend": trend,
                    "volume_spike": False,
                    "confidence": 0
                }

    except (IndexError, KeyError, ZeroDivisionError):
        return None

    return None
