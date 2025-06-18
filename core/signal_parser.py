# core/signal_parser.py

import MetaTrader5 as mt5
from datetime import datetime
import pandas as pd
import logging


def get_live_chart_state(symbol: str, timeframe=mt5.TIMEFRAME_M5, bars=500, return_df: bool = False) -> dict:
    """
    Fetch candles, indicators, and conditions for a given symbol.
    """

    # Ensure MT5 is initialized
    if not mt5.initialize():
        logging.error(f"❌ Failed to initialize MT5")
        return {}

    # Check if symbol is available and selected
    info = mt5.symbol_info(symbol)
    if info is None:
        logging.warning(f"⚠️ Symbol not found in MT5: {symbol}")
        return {}

    if not info.visible:
        selected = mt5.symbol_select(symbol, True)
        if not selected:
            logging.warning(f"⚠️ Could not make symbol visible: {symbol}")
            return {}

    # Fetch candle data
    rates = mt5.copy_rates_from_pos(symbol, timeframe, 0, bars)
    if rates is None or len(rates) == 0:
        logging.warning(f"⚠️ No candle data retrieved for {symbol} on timeframe {timeframe}")
        return {}

    df = pd.DataFrame(rates)
    df['time'] = pd.to_datetime(df['time'], unit='s')
    df.set_index('time', inplace=True)

    if df.empty or df.isnull().values.any():
        logging.warning(f"⚠️ DataFrame is empty or contains NaNs for {symbol}")
        return {}

    logging.info(f"📊 Retrieved {len(df)} bars for {symbol}")

    if return_df:
        return df

    # Fair Value Gaps (simple detection logic)
    fair_value_gaps = []
    for i in range(2, len(df)):
        if df['low'].iloc[i] > df['high'].iloc[i - 2]:  # Bullish gap
            fair_value_gaps.append({
                "price": float(df['low'].iloc[i]),
                "type": "bullish"
            })
        elif df['high'].iloc[i] < df['low'].iloc[i - 2]:  # Bearish gap
            fair_value_gaps.append({
                "price": float(df['high'].iloc[i]),
                "type": "bearish"
            })

    # Determine basic trend direction
    close_diff = df['close'].iloc[-1] - df['close'].iloc[0]
    trend = "up" if close_diff > 0 else "down"

    return {
        "candles": df[-50:].to_dict(orient="records"),
        "fair_value_gaps": fair_value_gaps,
        "trend": trend,
        "symbol": symbol,
        "timezone": str(datetime.now().astimezone().tzinfo),
        "volume_series": df["tick_volume"].tail(50).tolist()
    }
