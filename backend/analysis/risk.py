"""风险指标计算模块

基于日收益率序列计算 VaR、Sharpe、Max Drawdown、Beta 等风险指标。
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from backend.config import RISK_FREE_RATE, TRADING_DAYS_PER_YEAR
from backend.data.fetcher import fetch_index_daily


def compute_risk_metrics(df: pd.DataFrame, code: str) -> dict:
    """
    计算所有风险指标。

    Args:
        df: 日线数据 DataFrame，需含 close 列
        code: 股票代码

    Returns:
        { var_95, var_99, cvar_95, sharpe_ratio, max_drawdown, ... }
    """
    close = df["close"].astype(float).dropna()

    if len(close) < 20:
        return _empty_risk_result()

    # 日对数收益率
    returns = np.log(close / close.shift(1)).dropna()

    total_days = len(returns)

    # 年化收益率
    annual_return = float(returns.mean() * TRADING_DAYS_PER_YEAR)

    # 年化波动率
    annual_volatility = float(returns.std() * np.sqrt(TRADING_DAYS_PER_YEAR))

    # ── VaR & CVaR ──
    var_95 = float(np.percentile(returns, 5)) * 100   # 转为百分比
    var_99 = float(np.percentile(returns, 1)) * 100
    cvar_95 = float(returns[returns <= np.percentile(returns, 5)].mean()) * 100

    # ── Sharpe Ratio ──
    excess_return = annual_return - RISK_FREE_RATE
    sharpe_ratio = float(excess_return / annual_volatility) if annual_volatility > 0 else 0

    # ── Max Drawdown ──
    max_dd, max_dd_duration = _calc_max_drawdown(close)

    # ── Calmar Ratio ──
    calmar_ratio = float(annual_return / abs(max_dd)) if max_dd != 0 else 0

    # ── Win Rate ──
    win_rate = float((returns > 0).sum() / len(returns)) * 100

    # ── Beta ──
    beta = _calc_beta(returns, df["date"].iloc[0], df["date"].iloc[-1])

    return {
        "var_95": round(var_95, 3),
        "var_99": round(var_99, 3),
        "cvar_95": round(cvar_95, 3),
        "sharpe_ratio": round(sharpe_ratio, 3),
        "max_drawdown": round(max_dd * 100, 2),  # 转为百分比
        "max_drawdown_duration": max_dd_duration,
        "annual_volatility": round(annual_volatility * 100, 2),
        "annual_return": round(annual_return * 100, 2),
        "calmar_ratio": round(calmar_ratio, 3),
        "beta": round(beta, 3) if beta is not None else None,
        "win_rate": round(win_rate, 1),
        "total_days": total_days,
    }


def _calc_max_drawdown(close: pd.Series) -> tuple[float, int]:
    """计算最大回撤和最长回撤持续天数"""
    cumulative = (1 + close.pct_change().fillna(0)).cumprod()
    running_max = cumulative.cummax()
    drawdown = (cumulative - running_max) / running_max

    max_dd = float(drawdown.min())

    # 回撤持续期
    dd_start = None
    max_duration = 0
    for i, dd in enumerate(drawdown):
        if dd < 0 and dd_start is None:
            dd_start = i
        elif dd >= 0 and dd_start is not None:
            duration = i - dd_start
            max_duration = max(max_duration, duration)
            dd_start = None
    if dd_start is not None:
        duration = len(drawdown) - dd_start
        max_duration = max(max_duration, duration)

    return max_dd, max_duration


def _calc_beta(stock_returns: pd.Series, start_date: str, end_date: str) -> float | None:
    """计算相对上证指数的 Beta"""
    try:
        idx_df = fetch_index_daily("sh000001",
                                   start_date.replace("-", ""),
                                   end_date.replace("-", ""))
        if idx_df is None or idx_df.empty:
            return None

        idx_close = idx_df["close"].astype(float).dropna()
        idx_returns = np.log(idx_close / idx_close.shift(1)).dropna()

        # 对齐时间序列
        common_idx = stock_returns.index.intersection(idx_returns.index)
        if len(common_idx) < 20:
            # 尝试按长度对齐
            min_len = min(len(stock_returns), len(idx_returns))
            if min_len < 20:
                return None
            stock_aligned = stock_returns.iloc[-min_len:]
            idx_aligned = idx_returns.iloc[-min_len:]
        else:
            stock_aligned = stock_returns.loc[common_idx]
            idx_aligned = idx_returns.loc[common_idx]

        cov = np.cov(stock_aligned, idx_aligned)[0][1]
        var = np.var(idx_aligned)
        return float(cov / var) if var > 0 else None
    except Exception:
        return None


def _empty_risk_result() -> dict:
    return {
        "var_95": 0, "var_99": 0, "cvar_95": 0,
        "sharpe_ratio": 0, "max_drawdown": 0,
        "max_drawdown_duration": 0,
        "annual_volatility": 0, "annual_return": 0,
        "calmar_ratio": 0, "beta": None, "win_rate": 0,
        "total_days": 0,
    }
