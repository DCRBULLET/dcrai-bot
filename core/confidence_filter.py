# core/confidence_filter.py

import logging

# Define weight of each confidence factor
score_weights = {
    "high_conf_strategy": 2,
    "known_strategy": 1,
    "trend_alignment": 1,
    "rrr_ok": 1,
    # "volume_spike": 1,            # ⏳ Prep: Enable once volume analysis is added
    # "pattern_match": 1,          # ⏳ Prep: Enable once pattern system is added
    # "ai_confidence_match": 2     # ⏳ Prep: Enable once AI scoring is integrated
}

default_threshold = 3  # Can be customized per run


def filter_trade_by_confidence(trade_signal: dict, threshold: int = default_threshold, verbose: bool = True) -> dict:
    """
    Weighted confidence score system. Evaluates trade based on defined flags.
    Returns a dict with pass status, score, flags, and logs.
    """

    score = 0
    log = []
    flags = {}

    strategy = trade_signal.get("strategy")
    trend = trade_signal.get("trend")
    entry = trade_signal.get("entry")
    sl = trade_signal.get("sl")
    tp = trade_signal.get("tp")

    # 1. Strategy Confidence
    if strategy in {"fib_fvg", "inversion_fvg"}:
        flags["high_conf_strategy"] = True
        log.append("🧠 High-confidence strategy (+2)")
    elif strategy:
        flags["known_strategy"] = True
        log.append("📊 Recognized strategy (+1)")

    # 2. Trend Alignment
    if trend == "up" and entry and sl and entry > sl:
        flags["trend_alignment"] = True
        log.append("📈 Aligned with uptrend (+1)")
    elif trend == "down" and entry and sl and entry < sl:
        flags["trend_alignment"] = True
        log.append("📉 Aligned with downtrend (+1)")

    # 3. RRR Check
    if all([entry, sl, tp]):
        reward = abs(tp - entry)
        risk = abs(entry - sl)
        if risk > 0 and reward / risk >= 1.0:
            flags["rrr_ok"] = True
            log.append(f"💰 RRR OK ({reward:.2f}/{risk:.2f}) > 1 (+1)")
        else:
            log.append(f"⚠️ RRR low ({reward:.2f}/{risk:.2f})")
    else:
        log.append("❓ Missing entry/sl/tp for RRR check")

    # 4. Score Calculation
    for flag, weight in score_weights.items():
        if flags.get(flag):
            score += weight

    # Final Decision
    passed = score >= threshold
    if verbose:
        label = "✅ PASSED" if passed else "❌ REJECTED"
        logging.info(f"[Confidence Filter] {label} | Score: {score}/{sum(score_weights.values())}")
        for item in log:
            logging.info(f"  - {item}")

    return {
        "passed": passed,
        "score": score,
        "flags": flags,
        "log": log
    }


