from typing import Optional, Dict
import logging
import MetaTrader5 as mt5

from utils.helpers import pip_size, round_safe

def check_trade_opportunity(chart_data: Dict) -> Optional[Dict]:
    """
    Strategy: Fibonacci + Fair Value Gap with Volume Filter
    Looks for FVGs aligning with golden retracement zones (0.618–0.786).
    """
    if not mt5.initialize():
        logging.error("❌ MetaTrader 5 initialization failed.")
        return None

    candles = chart_data.get("candles", [])
    fair_value_gaps = chart_data.get("fair_value_gaps", [])
    trend = chart_data.get("trend")
    symbol = chart_data.get("symbol")
    volumes = chart_data.get("volume_series", [])

    if len(candles) < 50 or not fair_value_gaps or trend not in ["up", "down"] or symbol is None or len(volumes) < 11:
        return None

    logging.info(f"🔍 Trying to select symbol: {symbol}")
    if not mt5.symbol_select(symbol, True):
        available = [s.name for s in mt5.symbols_get()]
        logging.error(f"❌ Failed to select symbol '{symbol}'. Available: {available[:10]}")
        return None

    try:
        highs = [c["high"] for c in candles[-50:]]
        lows = [c["low"] for c in candles[-50:]]
        swing_high = max(highs)
        swing_low = min(lows)
        pip = pip_size(symbol)
        retracement_range = swing_high - swing_low

        recent_volume = volumes[-1]
        avg_volume = sum(volumes[-11:-1]) / 10
        if recent_volume < 0.8 * avg_volume:
            return None  # not enough conviction

        volume_spike = True  # for now just mark it true if passed above check

        if trend == "up":
            golden_min = swing_high - retracement_range * 0.786
            golden_max = swing_high - retracement_range * 0.618
            zone = (min(golden_min, golden_max), max(golden_min, golden_max))
            target = swing_high

            for fvg in fair_value_gaps:
                if fvg.get("type") != "bullish":
                    continue
                price = fvg.get("price")
                if price is None or not (zone[0] <= price <= zone[1]):
                    continue

                return {
                    "symbol": symbol,
                    "entry": round_safe(price, 3),
                    "sl": round_safe(zone[0] - (20 * pip), 3),
                    "tp": round_safe(target, 3),
                    "strategy": "fib_fvg",
                    "trend": trend,
                    "volume_spike": volume_spike,
                    "confidence": 0
                }

        elif trend == "down":
            golden_min = swing_low + retracement_range * 0.618
            golden_max = swing_low + retracement_range * 0.786
            zone = (min(golden_min, golden_max), max(golden_min, golden_max))
            target = swing_low

            for fvg in fair_value_gaps:
                if fvg.get("type") == "bullish":
                    continue
                price = fvg.get("price")
                if price is None or not (zone[0] <= price <= zone[1]):
                    continue

                return {
                    "symbol": symbol,
                    "entry": round_safe(price, 3),
                    "sl": round_safe(zone[1] + (20 * pip), 3),
                    "tp": round_safe(target, 3),
                    "strategy": "fib_fvg",
                    "trend": trend,
                    "volume_spike": volume_spike,
                    "confidence": 0
                }

    except (KeyError, IndexError, ZeroDivisionError):
        return None

    return None
