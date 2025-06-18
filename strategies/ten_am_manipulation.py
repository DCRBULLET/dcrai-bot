# strategies/ten_am_manipulation.py

import datetime as dt
import pandas as pd
import pytz
from typing import Optional, Dict
from utils.helpers import pip_size, round_safe

def detect_swing_lows(series: pd.Series) -> pd.Series:
    return series.rolling(window=3, center=True).apply(
        lambda x: x[1] if x[1] < x[0] and x[1] < x[2] else None
    ).dropna()

def detect_swing_highs(series: pd.Series) -> pd.Series:
    return series.rolling(window=3, center=True).apply(
        lambda x: x[1] if x[1] > x[0] and x[1] > x[2] else None
    ).dropna()

def check_trade_opportunity(chart_data: Dict) -> Optional[Dict]:
    """
    Strategy: 10AM Manipulation + BOS
    Detects liquidity sweep at 10AM IST followed by structure break.
    Returns standardized trade dictionary.
    """
    df: pd.DataFrame = chart_data.get("ohlcv")
    symbol: str = chart_data.get("symbol")
    timezone: str = chart_data.get("timezone", "Asia/Kolkata")
    trend: str = chart_data.get("trend")

    if df is None or len(df) < 50 or symbol is None:
        return None

    pip = pip_size(symbol)
    df = df.copy()

    if df.index.tz is None:
        df.index = df.index.tz_localize(pytz.utc).tz_convert(timezone)
    else:
        df.index = df.index.tz_convert(timezone)

    now = dt.datetime.now(pytz.timezone(timezone))
    session_date = now.date()

    session_start = dt.datetime.combine(session_date, dt.time(9, 45)).replace(tzinfo=pytz.timezone(timezone))
    session_end = dt.datetime.combine(session_date, dt.time(10, 15)).replace(tzinfo=pytz.timezone(timezone))

    session_df = df[(df.index >= session_start) & (df.index <= session_end)].copy()
    if len(session_df) < 5:
        return None

    high_before = session_df['high'].iloc[:-2].max()
    low_before = session_df['low'].iloc[:-2].min()
    last_candle = session_df.iloc[-1]

    if last_candle['high'] > high_before:
        swing_lows = detect_swing_lows(session_df['low'])
        if not swing_lows.empty:
            last_swing = swing_lows.iloc[-1]
            if last_candle['close'] < last_swing:
                sl = last_candle['high'] + 10 * pip
                tp = last_candle['close'] - 2 * (last_candle['close'] - last_swing)
                return {
                    "symbol": symbol,
                    "entry": round_safe(last_candle['close'], 3),
                    "sl": round_safe(sl, 3),
                    "tp": round_safe(tp, 3),
                    "strategy": "ten_am_manipulation",
                    "trend": trend,
                    "volume_spike": False,
                    "confidence": 0
                }

    elif last_candle['low'] < low_before:
        swing_highs = detect_swing_highs(session_df['high'])
        if not swing_highs.empty:
            last_swing = swing_highs.iloc[-1]
            if last_candle['close'] > last_swing:
                sl = last_candle['low'] - 10 * pip
                tp = last_candle['close'] + 2 * (last_swing - last_candle['close'])
                return {
                    "symbol": symbol,
                    "entry": round_safe(last_candle['close'], 3),
                    "sl": round_safe(sl, 3),
                    "tp": round_safe(tp, 3),
                    "strategy": "ten_am_manipulation",
                    "trend": trend,
                    "volume_spike": False,
                    "confidence": 0
                }

    return None
