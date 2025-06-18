# strategies/london_open_breakout.py

import datetime as dt
import pandas as pd
import pytz
from typing import Optional, Dict
from utils.helpers import pip_size, round_safe

def atr(df: pd.DataFrame, period: int = 14) -> float:
    high_low = df['high'] - df['low']
    high_close = (df['high'] - df['close'].shift()).abs()
    low_close = (df['low'] - df['close'].shift()).abs()
    tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
    return tr.rolling(period).mean().iloc[-1]

def has_upcoming_news(news_events: list, now: dt.datetime, window_minutes: int = 30) -> bool:
    for event in news_events:
        event_time = pd.to_datetime(event['time']).tz_localize('UTC')
        if abs((event_time - now).total_seconds()) <= window_minutes * 60:
            if event.get('impact', '').lower() == 'high':
                return True
    return False

def check_trade_opportunity(chart_data: Dict) -> Optional[Dict]:
    """
    Strategy: London Open Breakout
    With ATR, wick, RRR, and news filter.
    Returns standardized trade dictionary.
    """
    df: pd.DataFrame = chart_data.get("ohlcv")
    symbol = chart_data.get("symbol")
    trend = chart_data.get("trend")
    news = chart_data.get("news", [])
    timezone = chart_data.get("timezone", "UTC")

    if df is None or len(df) < 50 or symbol is None:
        return None

    df = df.copy()
    if df.index.tz is None:
        df.index = df.index.tz_localize(pytz.utc).tz_convert(timezone)
    else:
        df.index = df.index.tz_convert(timezone)

    now = dt.datetime.now(pytz.timezone(timezone))
    session_date = now.date()

    range_start = dt.datetime.combine(session_date, dt.time(7, 0)).replace(tzinfo=pytz.timezone(timezone))
    range_end = dt.datetime.combine(session_date, dt.time(8, 0)).replace(tzinfo=pytz.timezone(timezone))
    check_end = dt.datetime.combine(session_date, dt.time(9, 0)).replace(tzinfo=pytz.timezone(timezone))

    range_df = df[(df.index >= range_start) & (df.index < range_end)]
    confirm_df = df[(df.index >= range_end) & (df.index < check_end)]

    if len(range_df) < 3 or confirm_df.empty:
        return None

    if has_upcoming_news(news, now):
        return None

    high_range = range_df["high"].max()
    low_range = range_df["low"].min()
    pip = pip_size(symbol)

    avg_atr = atr(df[-50:])
    if (high_range - low_range) < 0.5 * avg_atr:
        return None

    for _, row in confirm_df.iterrows():
        wick_ratio = abs(row["high"] - row["close"]) / (row["high"] - row["low"] + 1e-6)
        if row["close"] > high_range and wick_ratio < 0.4:
            sl = low_range - 15 * pip
            tp = row["close"] + (row["close"] - sl)
            rrr = (tp - row["close"]) / (row["close"] - sl)
            if rrr >= 1.5:
                return {
                    "symbol": symbol,
                    "entry": round_safe(row["close"], 3),
                    "sl": round_safe(sl, 3),
                    "tp": round_safe(tp, 3),
                    "strategy": "london_open_breakout",
                    "trend": trend,
                    "volume_spike": False,
                    "confidence": 0
                }

    return None
