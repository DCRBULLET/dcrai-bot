import pandas as pd
from datetime import datetime
from utils.performance_tracker import PerformanceTracker
from utils.helpers import pip_size

class Backtester:
    def __init__(self, strategy, symbol: str, timeframe: str, ohlcv_data: pd.DataFrame):
        self.strategy = strategy
        self.symbol = symbol
        self.timeframe = timeframe
        self.ohlcv_data = ohlcv_data.copy()
        self.tracker = PerformanceTracker()

    def run(self):
        for i in range(50, len(self.ohlcv_data)):  # Start after warm-up
            candles = self.ohlcv_data.iloc[:i]
            chart_data = {
                "symbol": self.symbol,
                "timeframe": self.timeframe,
                "ohlcv": candles
            }

            try:
                signal = self.strategy.check_trade_opportunity(chart_data)
                if signal:
                    direction = signal.get("direction", "buy")
                    entry_price = signal.get("entry_price", candles.iloc[-1]["close"])
                    entry_time = candles.iloc[-1]["timestamp"]
                    exit_price = entry_price + 20 * pip_size(self.symbol) if direction == 'buy' else entry_price - 20 * pip_size(self.symbol)
                    exit_time = candles.iloc[-1]["timestamp"]
                    volume = signal.get("volume", 1.0)

                    pip = pip_size(self.symbol)
                    pnl_pips = (exit_price - entry_price) / pip if direction == 'buy' else (entry_price - exit_price) / pip
                    pnl = pnl_pips * volume

                    self.tracker.log_trade(
                        symbol=self.symbol,
                        direction=direction,
                        entry_time=entry_time,
                        entry_price=entry_price,
                        exit_time=exit_time,
                        exit_price=exit_price,
                        volume=volume,
                        pnl=pnl,
                        reason=self.strategy.__name__
                    )
            except Exception as e:
                print(f"[{self.strategy.__name__}] Backtest error at index {i}: {e}")

        return self.tracker
