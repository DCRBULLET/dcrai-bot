# utils/risk_engine.py

import logging
from utils.helpers import round_safe


def calculate_lot_size(balance: float, risk_percentage: float, stop_loss_pips: float, pip_value: float) -> float:
    """
    Calculate lot size based on account balance, risk percentage, stop loss in pips, and pip value.
    """
    if stop_loss_pips <= 0 or pip_value <= 0:
        raise ValueError("Stop loss and pip value must be greater than 0.")

    risk_amount = balance * (risk_percentage / 100)
    lot_size = risk_amount / (stop_loss_pips * pip_value)

    return round_safe(lot_size, 2)


def is_valid_risk_reward(risk_pips: float, reward_pips: float, min_rr: float = 1.5) -> bool:
    """
    Validate if the Reward:Risk ratio is acceptable.
    """
    if risk_pips <= 0 or reward_pips <= 0:
        return False

    rr_ratio = reward_pips / risk_pips
    return rr_ratio >= min_rr


def evaluate_trade_risk(
    entry: float,
    sl: float,
    tp: float,
    symbol: str,
    balance: float,
    risk_percent: float,
    pip_value: float,
    min_rr: float = 1.5,
    min_sl_pips: float = 10,
    max_sl_pips: float = 300,
    max_lot_size: float = 50,
    verbose: bool = False
) -> dict:
    """
    Evaluate the trade's risk, return decision, lot size, and reasoning.
    """
    sl_pips = abs(entry - sl) / pip_value
    tp_pips = abs(tp - entry) / pip_value

    if verbose:
        logging.info(f"[RiskEngine] SL Pips: {sl_pips:.2f}, TP Pips: {tp_pips:.2f}")

    if sl_pips < min_sl_pips:
        if verbose:
            logging.warning(f"[RiskEngine] ❌ SL too tight: {sl_pips:.2f} pips")
        return {"valid": False, "reason": f"Stop loss too tight ({sl_pips:.2f} pips)"}

    if sl_pips > max_sl_pips:
        if verbose:
            logging.warning(f"[RiskEngine] ❌ SL too wide: {sl_pips:.2f} pips")
        return {"valid": False, "reason": f"Stop loss too wide ({sl_pips:.2f} pips)"}

    if not is_valid_risk_reward(sl_pips, tp_pips, min_rr):
        rrr = tp_pips / sl_pips if sl_pips != 0 else 0
        if verbose:
            logging.warning(f"[RiskEngine] ❌ RRR too low: {rrr:.2f}")
        return {"valid": False, "reason": f"RRR too low ({rrr:.2f})"}

    lot_size = calculate_lot_size(balance, risk_percent, sl_pips, pip_value)

    if lot_size <= 0:
        if verbose:
            logging.warning("[RiskEngine] ❌ Calculated lot size is 0 or negative.")
        return {"valid": False, "reason": "Calculated lot size is 0 or negative."}

    if lot_size > max_lot_size:
        if verbose:
            logging.warning(f"[RiskEngine] ❌ Lot size too large: {lot_size:.2f}")
        return {"valid": False, "reason": f"Lot size too large ({lot_size:.2f})"}

    return {
        "valid": True,
        "lot_size": lot_size,
        "sl_pips": round_safe(sl_pips, 1),
        "tp_pips": round_safe(tp_pips, 1),
        "rrr": round_safe(tp_pips / sl_pips, 2),
    }
