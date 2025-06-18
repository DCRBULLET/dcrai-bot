# core/trade_executor.py

import MetaTrader5 as mt5
import logging
from utils.helpers import round_safe, pip_size
from core.telegram_alert import send_trade_alert  # Alert system for real-time notification
from utils.risk_engine import evaluate_trade_risk

logging.basicConfig(level=logging.INFO)

def execute_trade(signal: dict, trade_id: str = None):
    """
    Execute a trade via MetaTrader 5.
    Automatically calculates SL/TP distances & sends Telegram alert.
    Integrates with risk engine.
    """
    symbol = signal["symbol"]
    entry_price = signal["entry"]
    sl = signal["sl"]
    tp = signal["tp"]
    strategy = signal.get("strategy", "unknown")

    account = mt5.account_info()
    if account is None or account.balance < 5:
        logging.warning("💸 Skipping trade: Not enough balance or no account info.")
        return {
            "status": "failed",
            "symbol": symbol,
            "strategy": strategy,
            "reason": "No balance or account info"
        }

    pip_val = pip_size(symbol)
    risk_check = evaluate_trade_risk(
        entry=entry_price,
        sl=sl,
        tp=tp,
        symbol=symbol,
        balance=account.balance,
        risk_percent=1.0,  # You can make this configurable
        pip_value=pip_val
    )

    if not risk_check.get("valid"):
        logging.info(f"❌ Trade rejected: {risk_check['reason']}")
        return {"status": "rejected", "reason": risk_check['reason']}

    lot = max(0.01, risk_check['lot_size'])

    if not mt5.symbol_select(symbol, True):
        raise RuntimeError(f"❌ Failed to select symbol {symbol}")

    info = mt5.symbol_info(symbol)
    if info is None:
        raise RuntimeError(f"❌ Could not get symbol info for {symbol}")

    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        raise RuntimeError(f"❌ No tick data available for {symbol}")

    min_vol = info.volume_min
    max_vol = info.volume_max
    vol_step = info.volume_step
    lot = max(min_vol, round(lot / vol_step) * vol_step)
    if lot < min_vol or lot > max_vol:
        lot = min_vol

    is_buy = tp > entry_price
    price = tick.ask if is_buy else tick.bid

    point = info.point
    stops_level = getattr(info, 'stops_level', 0)
    min_distance = stops_level * point if stops_level else (1.5 if "XAU" in symbol else 0.00030)

    sl_diff = abs(price - sl)
    tp_diff = abs(tp - price)

    sl_final = price - max(sl_diff, min_distance) if is_buy else price + max(sl_diff, min_distance)
    tp_final = price + max(tp_diff, min_distance) if is_buy else price - max(tp_diff, min_distance)

    request = {
        "action": mt5.TRADE_ACTION_DEAL,
        "symbol": symbol,
        "volume": lot,
        "type": mt5.ORDER_TYPE_BUY if is_buy else mt5.ORDER_TYPE_SELL,
        "price": price,
        "sl": round(sl_final, info.digits),
        "tp": round(tp_final, info.digits),
        "deviation": 10,
        "magic": 444000 + hash(strategy) % 1000,
        "comment": f"DCRAI_{strategy}_{trade_id or 'AUTO'}",
        "type_time": mt5.ORDER_TIME_GTC,
        "type_filling": mt5.ORDER_FILLING_IOC
    }

    result = mt5.order_send(request)

    if result.retcode != mt5.TRADE_RETCODE_DONE:
        logging.error(f"❌ Trade failed: [{result.retcode}] {result.comment}")
        return {
            "status": "failed",
            "symbol": symbol,
            "strategy": strategy,
            "price": price,
            "sl": sl_final,
            "tp": tp_final,
            "reason": result.comment,
            "retcode": result.retcode
        }

    logging.info(f"✅ Trade executed: Ticket #{result.order} | {symbol} @ {price:.3f}")

    send_trade_alert({
        "symbol": symbol,
        "price": round_safe(price, 3),
        "sl": round_safe(sl_final, 3),
        "tp": round_safe(tp_final, 3),
        "lot": lot,
        "strategy": strategy,
        "order_id": result.order,
        "direction": "Buy" if is_buy else "Sell"
    })

    return {
        "status": "success",
        "symbol": symbol,
        "strategy": strategy,
        "order_id": result.order,
        "price": round_safe(price, 3),
        "sl": round_safe(sl_final, 3),
        "tp": round_safe(tp_final, 3),
        "volume": lot,
        "trade_id": trade_id
    }

