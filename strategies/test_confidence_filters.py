import logging
from core.signal_parser import get_live_chart_state
from strategies import fib_fvg  # Use any strategy you'd like to test
from core.confidence_filter import filter_trade_by_confidence

# Setup logging to show everything
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Get chart data
chart_data = get_live_chart_state()
symbols = list(chart_data.keys())
print(f"🧪 Testing on {len(symbols)} symbols")

# Test on first few symbols only
for symbol in symbols[:10]:
    candles = chart_data[symbol]
    trade = fib_fvg.generate_trade(symbol, candles)

    if not trade:
        print(f"⛔ No trade signal generated for {symbol}")
        continue

    print(f"\n🎯 Testing strategy output on: {symbol}")
    print(f"📋 Trade candidate: {trade}")

    passed, score, log = filter_trade_by_confidence(trade, verbose=True)
    print(f"✅ PASSED: {passed} | Score: {score}/5")
    for reason in log:
        print(f"  - {reason}")
