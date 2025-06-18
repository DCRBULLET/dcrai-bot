import logging
import MetaTrader5 as mt5

def get_active_symbols() -> list[str]:
    logging.info("🔍 Running get_active_symbols...")

    if not mt5.initialize():
        logging.error("❌ MT5 initialization failed")
        return []

    all_symbols = mt5.symbols_get()
    if not all_symbols:
        logging.error("❌ No symbols retrieved from MT5.")
        return []

    tradable = []
    for s in all_symbols:
        if s.visible and s.trade_mode in (
            mt5.SYMBOL_TRADE_MODE_FULL,
            mt5.SYMBOL_TRADE_MODE_LONGONLY,
            mt5.SYMBOL_TRADE_MODE_SHORTONLY
        ):
            tradable.append(s.name)

    logging.info(f"✅ Found {len(tradable)} tradable symbols.")

    mt5.shutdown()  # Optional: Shuts down MT5 to keep things clean.
    return tradable

