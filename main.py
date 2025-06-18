import logging
import time
import schedule
import traceback
import pandas as pd
from datetime import datetime, timedelta

import MetaTrader5 as mt5

from strategies import (
    fib_fvg,
    inversion_fvg,
    volume_liquidity,
    doji_confirmation,
    london_open_breakout,
    ten_am_manipulation
)

from core.signal_parser import get_live_chart_state
from core.confidence_filter import filter_trade_by_confidence
from core.trade_executor import execute_trade
from core.symbol_scanner import get_active_symbols
from core.trade_manager import trail_stop_loss, breakeven_stop_loss
from core.config_loader import get_strategy_map, get_cooldown_minutes, get_max_trade_duration
from core.telegram_alert import send_trade_alert
from utils.performance_tracker import PerformanceTracker
from utils.risk_engine import calculate_lot_size
from utils.helpers import pip_size

# 🪵 Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

performance_tracker = PerformanceTracker()

strategy_lookup = {
    "fib_fvg": fib_fvg,
    "inversion_fvg": inversion_fvg,
    "volume_liquidity": volume_liquidity,
    "doji_confirmation": doji_confirmation,
    "london_open_breakout": london_open_breakout,
    "ten_am_manipulation": ten_am_manipulation
}

strategy_map = get_strategy_map()
cooldown_tracker = {}

def run_dcrai_strategy_engine():
    logging.info("🚀 Running DCRAI strategy engine")
    symbols = get_active_symbols()

    for symbol in symbols:
        logging.info(f"🔍 Scanning symbol: {symbol}")
        try:
            chart_data = get_live_chart_state(symbol)
            if not chart_data:
                continue

            # 🧠 Inject all required components
            chart_data["symbol"] = symbol
            chart_data["timezone"] = str(datetime.now().astimezone().tzinfo)
            chart_data["volume_series"] = [c["tick_volume"] for c in chart_data["candles"]][-50:]
            chart_data["ohlcv"] = pd.DataFrame(chart_data["candles"]).set_index("time")
            chart_data["news"] = []

            mapped_strategies = strategy_map.get(symbol, [])

            for strategy_name in mapped_strategies:
                strategy = strategy_lookup[strategy_name]
                key = f"{symbol}_{strategy_name}"

                # ⏳ Cooldown check
                last_time = cooldown_tracker.get(key)
                cooldown = get_cooldown_minutes(strategy_name)
                if last_time and datetime.now() - last_time < timedelta(minutes=cooldown):
                    logging.info(f"⏳ Skipping {key} due to cooldown.")
                    continue

                try:
                    trade = strategy.check_trade_opportunity(chart_data)
                    if trade is None:
                        continue

                    # ✅ Validate trade dictionary structure
                    required_keys = {"symbol", "entry", "sl", "tp", "type", "strategy_name"}
                    if not required_keys.issubset(trade):
                        logging.error(f"❌ Invalid trade dictionary from {strategy_name}: {trade}")
                        continue

                    # 🧠 Apply confidence filter
                    if "confidence" not in trade:
                        trade["confidence"] = 0
                    filter_result = filter_trade_by_confidence(trade)
                    if not filter_result["passed"]:
                        continue
                    trade["confidence"] = filter_result["score"]

                    # 📏 Risk-based lot sizing
                    balance = mt5.account_info().balance
                    risk_pct = 1.0  # Or load from config
                    sl_pips = abs(trade["entry"] - trade["sl"]) / pip_size(trade["symbol"])
                    pip_val = 10  # Approximate placeholder
                    lot = calculate_lot_size(balance, risk_pct, sl_pips, pip_val)
                    trade["lot"] = lot

                    # 🛠️ Execute trade
                    result = execute_trade(trade)

                    if result:
                        performance_tracker.record_trade(trade, result)
                        cooldown_tracker[key] = datetime.now()
                        send_trade_alert(trade)
                    else:
                        logging.error("❌ Trade execution failed.")

                except Exception as e:
                    logging.error(f"⚠️ Error in strategy {strategy_name}: {e}\n{traceback.format_exc()}")

        except Exception as e:
            logging.error(f"❌ Failed to process symbol {symbol}: {e}\n{traceback.format_exc()}")

    # 📊 Log performance summary
    logging.info("\n" + performance_tracker.get_summary())


def run_trade_manager():
    logging.info("🛠️ Running trade manager for open trades")
    symbols = get_active_symbols()
    max_duration = get_max_trade_duration()

    for symbol in symbols:
        try:
            positions = mt5.positions_get(symbol=symbol)
            if positions is None:
                continue
            for pos in positions:
                # ⏰ Max duration auto-close
                open_time = pos.time
                open_dt = datetime.fromtimestamp(open_time)
                if datetime.now() - open_dt > timedelta(minutes=max_duration):
                    logging.info(f"⏰ Closing trade on {symbol} due to max duration.")
                    close_request = {
                        "action": mt5.TRADE_ACTION_DEAL,
                        "symbol": symbol,
                        "volume": pos.volume,
                        "type": mt5.ORDER_SELL if pos.type == 0 else mt5.ORDER_BUY,
                        "position": pos.ticket,
                        "deviation": 10,
                        "magic": pos.magic,
                        "comment": "Auto-close due to duration limit"
                    }
                    result = mt5.order_send(close_request)
                    if result.retcode != mt5.TRADE_RETCODE_DONE:
                        logging.error(f"❌ Failed to auto-close trade: {result.retcode}")
                    continue

                # 📈 SL trail & breakeven
                entry = pos.price_open
                direction = "buy" if pos.type == 0 else "sell"
                sl = pos.sl
                trail_stop_loss(symbol, entry, sl, direction, 20, 15)
                breakeven_stop_loss(symbol, entry, direction, 25)

        except Exception as e:
            logging.error(f"❌ Trade manager error for {symbol}: {e}")


# 🔄 Schedule
schedule.every(15).minutes.do(run_dcrai_strategy_engine)
schedule.every(1).minutes.do(run_trade_manager)

# 🧠 Start
if __name__ == "__main__":
    try:
        run_dcrai_strategy_engine()
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logging.info("🛑 DCRAI BOT stopped by user.")
        exit()
