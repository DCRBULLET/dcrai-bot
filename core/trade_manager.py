# core/trade_manager.py

import logging
import MetaTrader5 as mt5
from utils.helpers import pip_size

logging.basicConfig(level=logging.INFO)

def trail_stop_loss(symbol: str, entry_price: float, sl_price: float, direction: str,
                    trail_trigger_pips: float, trail_distance_pips: float) -> bool:
    """
    Adjust stop loss when price moves in favor beyond trigger.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logging.error(f"❌ Failed to get tick data for {symbol}")
        return False

    current_price = tick.ask if direction == "buy" else tick.bid
    pip = pip_size(symbol)

    profit_pips = (current_price - entry_price) / pip if direction == "buy" else (entry_price - current_price) / pip

    if profit_pips >= trail_trigger_pips:
        new_sl = current_price - trail_distance_pips * pip if direction == "buy" else current_price + trail_distance_pips * pip

        if (direction == "buy" and new_sl > sl_price) or (direction == "sell" and new_sl < sl_price):
            positions = mt5.positions_get(symbol=symbol)
            for pos in positions:
                if pos.symbol == symbol and pos.type == (0 if direction == "buy" else 1):
                    result = mt5.order_send({
                        "action": mt5.TRADE_ACTION_SLTP,
                        "position": pos.ticket,
                        "sl": new_sl,
                        "tp": pos.tp,
                    })
                    if result.retcode == mt5.TRADE_RETCODE_DONE:
                        logging.info(f"🔄 Trailing SL updated for {symbol} | Ticket: {pos.ticket} | New SL: {new_sl}")
                        return True
                    else:
                        logging.error(f"❌ Failed to update trailing SL for {symbol} | Ticket: {pos.ticket} | Code: {result.retcode}")
                        return False
        else:
            logging.info(f"⚠️ SL unchanged for {symbol} — new SL not better than current.")
    return False


def breakeven_stop_loss(symbol: str, entry_price: float, direction: str, trigger_pips: float) -> bool:
    """
    Move SL to breakeven after certain pip profit.
    """
    tick = mt5.symbol_info_tick(symbol)
    if tick is None:
        logging.error(f"❌ Failed to get tick data for {symbol}")
        return False

    pip = pip_size(symbol)
    current_price = tick.ask if direction == "buy" else tick.bid

    profit_pips = (current_price - entry_price) / pip if direction == "buy" else (entry_price - current_price) / pip

    if profit_pips >= trigger_pips:
        new_sl = entry_price
        positions = mt5.positions_get(symbol=symbol)
        for pos in positions:
            if pos.symbol == symbol and pos.type == (0 if direction == "buy" else 1):
                result = mt5.order_send({
                    "action": mt5.TRADE_ACTION_SLTP,
                    "position": pos.ticket,
                    "sl": new_sl,
                    "tp": pos.tp,
                })
                if result.retcode == mt5.TRADE_RETCODE_DONE:
                    logging.info(f"🟩 SL moved to breakeven for {symbol} | Ticket: {pos.ticket}")
                    return True
                else:
                    logging.error(f"❌ Failed to move SL to breakeven for {symbol} | Ticket: {pos.ticket} | Code: {result.retcode}")
                    return False
    return False
