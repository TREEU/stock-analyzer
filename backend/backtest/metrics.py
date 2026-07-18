"""回测绩效指标计算"""

import numpy as np
import pandas as pd
from backend.config import TRADING_DAYS_PER_YEAR, RISK_FREE_RATE


def compute_metrics(
    trades: list[dict],
    equity_curve: list[dict],
    benchmark_equity: list[dict],
) -> dict:
    """
    根据交易记录和权益曲线计算所有绩效指标。

    Args:
        trades: 交易记录列表
        equity_curve: 策略权益曲线 [{date, equity}, ...]
        benchmark_equity: 基准权益曲线 [{date, equity}, ...]

    Returns:
        绩效指标字典
    """
    if not equity_curve:
        return _empty_metrics()

    # 权益序列
    equity_values = np.array([e["equity"] for e in equity_curve])
    initial_capital = equity_values[0]
    final_equity = equity_values[-1]
    n_days = len(equity_values)

    # ── 收益指标 ──
    total_return = (final_equity - initial_capital) / initial_capital
    annual_return = (1 + total_return) ** (TRADING_DAYS_PER_YEAR / max(n_days, 1)) - 1

    # 基准收益
    benchmark_return = 0.0
    if benchmark_equity:
        bench_values = np.array([e["equity"] for e in benchmark_equity])
        benchmark_return = (bench_values[-1] - bench_values[0]) / bench_values[0]

    excess_return = total_return - benchmark_return

    # ── Sharpe Ratio ──
    daily_returns = np.diff(equity_values) / equity_values[:-1]
    sharpe = 0.0
    if len(daily_returns) > 1 and daily_returns.std() > 0:
        sharpe = float((daily_returns.mean() * TRADING_DAYS_PER_YEAR - RISK_FREE_RATE)
                       / (daily_returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR)))

    # ── Max Drawdown ──
    cumulative = equity_values / equity_values[0]
    running_max = np.maximum.accumulate(cumulative)
    drawdowns = (cumulative - running_max) / running_max
    max_dd = float(drawdowns.min())

    # ── 交易统计 ──
    if trades:
        pnls = [t.get("pnl_pct", 0) or 0 for t in trades if t.get("action") == "sell"]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        win_rate = len(wins) / len(pnls) if pnls else 0
        avg_win = np.mean(wins) if wins else 0
        avg_loss = np.mean(losses) if losses else 0

        gross_profit = sum(wins)
        gross_loss = abs(sum(losses))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float("inf")

        # 最大连续亏损
        max_consecutive_losses = 0
        current_streak = 0
        for p in pnls:
            if p <= 0:
                current_streak += 1
                max_consecutive_losses = max(max_consecutive_losses, current_streak)
            else:
                current_streak = 0

        # 期望值
        expectancy = (win_rate * avg_win) - ((1 - win_rate) * abs(avg_loss))
    else:
        win_rate = 0
        avg_win = 0
        avg_loss = 0
        profit_factor = 0
        max_consecutive_losses = 0
        expectancy = 0

    return {
        "total_return": round(float(total_return) * 100, 2),
        "annual_return": round(float(annual_return) * 100, 2),
        "benchmark_return": round(float(benchmark_return) * 100, 2),
        "excess_return": round(float(excess_return) * 100, 2),
        "sharpe_ratio": round(float(sharpe), 3),
        "max_drawdown": round(float(max_dd) * 100, 2),
        "win_rate": round(float(win_rate) * 100, 1),
        "profit_factor": round(float(profit_factor), 2),
        "avg_win": round(float(avg_win) * 100, 2),
        "avg_loss": round(float(avg_loss) * 100, 2),
        "total_trades": len([t for t in trades if t.get("action") == "sell"]),
        "max_consecutive_losses": max_consecutive_losses,
        "expectancy": round(float(expectancy) * 100, 2),
    }


def _empty_metrics() -> dict:
    return {
        "total_return": 0, "annual_return": 0, "benchmark_return": 0,
        "excess_return": 0, "sharpe_ratio": 0, "max_drawdown": 0,
        "win_rate": 0, "profit_factor": 0, "avg_win": 0, "avg_loss": 0,
        "total_trades": 0, "max_consecutive_losses": 0, "expectancy": 0,
    }
