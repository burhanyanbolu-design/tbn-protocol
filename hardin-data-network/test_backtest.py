import sys
sys.path.insert(0, '/opt/vc3')
import backtester
print("Running backtest...")
r = backtester.run_backtest(start="2024-01-01", end="2024-03-31")
print("Keys:", list(r.keys()))
print("Total trades:", r.get("total_trades"))
print("Total PnL:", r.get("total_pnl"))
print("Win rate:", r.get("win_rate"))
