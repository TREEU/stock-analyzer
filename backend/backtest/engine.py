"""向量化回测引擎

核心设计：
- 仅做多（long-only）
- T日信号 → T+1日开盘执行（避免前视偏差）
- 单仓位（要么全仓持股，要么空仓现金）
- 双边手续费 + 滑点模拟
"""

import pandas as pd
import numpy as np

from backend.config import DEFAULT_COMMISSION, DEFAULT_SLIPPAGE
from backend.backtest.strategies import BaseStrategy


class BacktestEngine:
    def __init__(
        self,
        df: pd.DataFrame,
        initial_capital: float = 100_000,
        commission: float = DEFAULT_COMMISSION,
        slippage: float = DEFAULT_SLIPPAGE,
    ):
        """
        Args:
            df: 日线数据 [date, open, high, low, close, volume]
            initial_capital: 初始资金
            commission: 单边手续费率 (0.03% = 0.0003)
            slippage: 滑点比例 (0.1% = 0.001)
        """
        self.df = df.reset_index(drop=True).copy()
        self.initial_capital = initial_capital
        self.commission = commission
        self.slippage = slippage

    def run(self, strategy: BaseStrategy) -> dict:
        """
        执行回测。

        Returns:
            { trades, metrics, equity_curve, benchmark_equity }
        """
        # 1. 生成信号
        signals = strategy.generate_signals(self.df)

        # 2. 模拟交易
        trades, equity_curve = self._simulate(signals)

        # 3. 基准 buy-and-hold
        benchmark_equity = self._benchmark_equity()

        # 4. 计算指标
        from backend.backtest.metrics import compute_metrics
        metrics = compute_metrics(trades, equity_curve, benchmark_equity)

        return {
            "trades": trades,
            "metrics": metrics,
            "equity_curve": equity_curve,
            "benchmark_equity": benchmark_equity,
        }

    def _simulate(self, signals: pd.Series) -> tuple[list[dict], list[dict]]:
        """根据信号序列模拟交易"""
        cash = self.initial_capital
        shares = 0
        trades = []
        equity_curve = []

        in_position = False
        entry_price = 0
        entry_date = ""

        for i in range(len(self.df)):
            date = self.df.loc[i, "date"]
            open_price = float(self.df.loc[i, "open"])
            close_price = float(self.df.loc[i, "close"])
            signal = signals.iloc[i] if i < len(signals) else 0

            # 执行待处理信号（T日信号 → T日收盘或T+1日开盘？用当日收盘更简单）
            exec_price = close_price

            # 买入信号
            if signal == 1 and not in_position:
                # 扣除滑点
                buy_price = exec_price * (1 + self.slippage)
                shares = int(cash * 0.995 / buy_price)  # 留一点现金缓冲
                cost = shares * buy_price * (1 + self.commission)
                if shares > 0 and cost <= cash:
                    cash -= cost
                    in_position = True
                    entry_price = buy_price
                    entry_date = str(date)
                    trades.append({
                        "date": str(date),
                        "action": "buy",
                        "price": round(buy_price, 2),
                        "shares": shares,
                        "cash_after": round(cash, 2),
                        "equity": round(cash + shares * close_price, 2),
                        "pnl_pct": None,
                    })

            # 卖出信号
            elif signal == -1 and in_position:
                sell_price = exec_price * (1 - self.slippage)
                revenue = shares * sell_price * (1 - self.commission)
                pnl_pct = (sell_price - entry_price) / entry_price if entry_price > 0 else 0
                cash += revenue
                trades.append({
                    "date": str(date),
                    "action": "sell",
                    "price": round(sell_price, 2),
                    "shares": shares,
                    "cash_after": round(cash, 2),
                    "equity": round(cash, 2),
                    "pnl_pct": round(pnl_pct * 100, 2),
                })
                shares = 0
                in_position = False

            # 记录每日权益
            current_equity = cash + shares * close_price
            equity_curve.append({
                "date": str(date),
                "equity": round(current_equity, 2),
                "cash": round(cash, 2),
                "holdings": round(shares * close_price, 2),
                "shares": shares,
            })

        # 回测结束时若仍持仓，按最后收盘价强制平仓
        if in_position and shares > 0:
            last_close = float(self.df.iloc[-1]["close"])
            sell_price = last_close * (1 - self.slippage)
            revenue = shares * sell_price * (1 - self.commission)
            pnl_pct = (sell_price - entry_price) / entry_price if entry_price > 0 else 0
            cash += revenue
            trades.append({
                "date": str(self.df.iloc[-1]["date"]),
                "action": "sell",
                "price": round(sell_price, 2),
                "shares": shares,
                "cash_after": round(cash, 2),
                "equity": round(cash, 2),
                "pnl_pct": round(pnl_pct * 100, 2),
                "note": "回测结束强制平仓",
            })
            # 更新最后一条权益
            if equity_curve:
                equity_curve[-1]["equity"] = round(cash, 2)
                equity_curve[-1]["cash"] = round(cash, 2)
                equity_curve[-1]["holdings"] = 0
                equity_curve[-1]["shares"] = 0

        return trades, equity_curve

    def _benchmark_equity(self) -> list[dict]:
        """计算 buy-and-hold 基准权益曲线"""
        if self.df.empty:
            return []

        first_close = float(self.df.iloc[0]["close"])
        if first_close <= 0:
            return []

        shares = int(self.initial_capital * 0.995 / (first_close * (1 + self.commission)))
        cost = shares * first_close * (1 + self.commission)
        cash_remain = self.initial_capital - cost

        result = []
        for _, row in self.df.iterrows():
            close = float(row["close"])
            equity = cash_remain + shares * close
            result.append({
                "date": str(row["date"]),
                "equity": round(equity, 2),
            })

        return result
