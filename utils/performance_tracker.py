import logging
from datetime import datetime
from collections import defaultdict

class PerformanceTracker:
    def __init__(self):
        self.trades = []

    def record_trade(self, trade: dict, result: dict):
        """
        Records a completed trade with its result.
        """
        record = {
            "symbol": trade.get("symbol"),
            "entry": trade.get("entry"),
            "sl": trade.get("sl"),
            "tp": trade.get("tp"),
            "strategy": trade.get("strategy"),
            "confidence": trade.get("confidence"),
            "volume_spike": trade.get("volume_spike"),
            "trend": trade.get("trend"),
            "ticket": result.get("ticket"),
            "price": result.get("price"),
            "time": result.get("time", str(datetime.now())),
            "result": result.get("result"),
            "rrr": result.get("rrr", 0),
            "pnl": result.get("pnl", 0),
        }
        self.trades.append(record)
        logging.info(f"📊 Trade recorded: {record}")

    def get_summary(self):
        """
        Returns a formatted performance summary.
        """
        if not self.trades:
            return "📉 No trades to summarize."

        total = len(self.trades)
        wins = sum(1 for t in self.trades if t["result"] == "win")
        losses = sum(1 for t in self.trades if t["result"] == "loss")
        breakevens = sum(1 for t in self.trades if t["result"] == "breakeven")
        total_pnl = sum(t["pnl"] for t in self.trades)
        avg_rrr = sum(t["rrr"] for t in self.trades if t["rrr"] > 0) / max(wins + losses, 1)
        profit_factor = sum(t["pnl"] for t in self.trades if t["pnl"] > 0) / abs(sum(t["pnl"] for t in self.trades if t["pnl"] < 0) or 1)

        strategy_stats = defaultdict(int)
        symbol_stats = defaultdict(int)
        for t in self.trades:
            strategy_stats[t["strategy"]] += 1
            symbol_stats[t["symbol"]] += 1

        summary = [
            "📈 **Performance Summary**",
            f"• Total Trades: {total}",
            f"• Wins: {wins} | Losses: {losses} | Breakevens: {breakevens}",
            f"• Win Rate: {wins / total * 100:.2f}%",
            f"• Average RRR: {avg_rrr:.2f}",
            f"• Profit Factor: {profit_factor:.2f}",
            f"• Total PnL: {total_pnl:.2f}",
            "",
            "📊 Strategy Breakdown:"
        ]

        for strategy, count in strategy_stats.items():
            summary.append(f"   - {strategy}: {count} trades")

        summary.append("\n📍 Symbol Breakdown:")
        for symbol, count in symbol_stats.items():
            summary.append(f"   - {symbol}: {count} trades")

        return "\n".join(summary)

    def get_daily_summary(self, date_str: str = None) -> str:
        """
        Returns a summary for trades placed on a specific date.
        """
        if not self.trades:
            return "📉 No trades to summarize."

        if not date_str:
            date_str = datetime.now().strftime("%Y-%m-%d")

        day_trades = [t for t in self.trades if t["time"].startswith(date_str)]
        if not day_trades:
            return f"📅 No trades on {date_str}"

        total = len(day_trades)
        wins = sum(1 for t in day_trades if t["result"] == "win")
        losses = sum(1 for t in day_trades if t["result"] == "loss")
        breakevens = sum(1 for t in day_trades if t["result"] == "breakeven")
        total_pnl = sum(t["pnl"] for t in day_trades)
        avg_rrr = sum(t["rrr"] for t in day_trades if t["rrr"] > 0) / max(wins + losses, 1)
        profit_factor = sum(t["pnl"] for t in day_trades if t["pnl"] > 0) / abs(sum(t["pnl"] for t in day_trades if t["pnl"] < 0) or 1)

        summary = [
            f"📅 **Daily Performance Summary ({date_str})**",
            f"• Total Trades: {total}",
            f"• Wins: {wins} | Losses: {losses} | Breakevens: {breakevens}",
            f"• Win Rate: {wins / total * 100:.2f}%",
            f"• Average RRR: {avg_rrr:.2f}",
            f"• Profit Factor: {profit_factor:.2f}",
            f"• Total PnL: {total_pnl:.2f}",
        ]

        return "\n".join(summary)

    def export_trades_to_csv(self, filename="trades.csv"):
        import csv
        keys = self.trades[0].keys() if self.trades else []
        with open(filename, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(self.trades)
