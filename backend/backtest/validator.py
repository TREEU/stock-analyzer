"""综合回测验证器

一次验证做四件事：
1. 7 种策略同时跑 → 横向对比
2. 划分牛市/熊市/震荡市 → 看在不同行情下的表现
3. 滚动窗口 → 不是只看一个时间段
4. 参数敏感性 → 看看参数调一下结果天差地别还是稳定
"""
from __future__ import annotations

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from backend.data.fetcher import fetch_daily_price
from backend.backtest.engine import BacktestEngine
from backend.backtest.strategies import STRATEGY_REGISTRY


def comprehensive_validate(code: str, start: str = "20210101",
                           end: str = "") -> dict:
    """全面验证一只股票的策略表现（支持自定义时间范围）"""
    df = fetch_daily_price(code, start, end)
    if df is None or df.empty or len(df) < 15:
        return {"error": f"数据仅{len(df) if df is not None else 0}个交易日，至少需要15个（约3周）"}

    close = df["close"].astype(float)
    current_price = float(close.iloc[-1])

    # 先跑策略排名，找到最优策略
    comparison = _compare_all_strategies(df)
    best_name = comparison.get("best_strategy", "ma_cross")
    best_params = comparison.get("rankings", [{}])[0].get("params", {})

    # 计算 buy-and-hold 基准（持有整个时间段不动）
    first_close = float(df.iloc[0]["close"])
    last_close = float(df.iloc[-1]["close"])
    buy_hold_return = round((last_close / first_close - 1) * 100, 2)

    return {
        "code": code,
        "current_price": round(current_price, 2),
        "first_price": round(first_close, 2),
        "data_range": f"{df.iloc[0]['date']} ~ {df.iloc[-1]['date']}",
        "total_days": len(df),
        "buy_hold_return": buy_hold_return,
        # 1. 多策略横向对比
        "strategy_comparison": comparison,
        # 2. 不同市场环境（用最优策略）
        "market_regimes": _regime_analysis(df, best_name, best_params),
        # 3. 滚动窗口验证（用最优策略）
        "rolling_validation": _rolling_window(df, best_name, best_params),
        # 4. 参数敏感性（测最优策略的参数）
        "parameter_sensitivity": _sensitivity_test(df, best_name),
    }


def _compare_all_strategies(df: pd.DataFrame) -> dict:
    """7种策略同时跑，横向排名"""
    results = []
    for name, cls in STRATEGY_REGISTRY.items():
        params = cls.default_params()
        strategy = cls(**params)
        engine = BacktestEngine(df, initial_capital=100_000)
        try:
            result = engine.run(strategy)
            metrics = result["metrics"]
            metrics["strategy"] = name
            metrics["params"] = params
            results.append(metrics)
        except Exception:
            continue

    if not results:
        return {"error": "无法运行策略"}

    # 综合排名：50% 超额收益 + 30% Sharpe + 20% (1 - |最大回撤|)
    for r in results:
        excess = r.get("excess_return", 0) / 100  # 转小数
        sharpe = max(r.get("sharpe_ratio", -1), -1)
        maxdd = min(abs(r.get("max_drawdown", 0)) / 100, 1)
        r["composite_score"] = round(
            excess * 0.5 + (sharpe / 3) * 0.3 + (1 - maxdd) * 0.2, 4
        )

    results.sort(key=lambda x: x["composite_score"], reverse=True)

    return {
        "rankings": [
            {
                "rank": i + 1,
                "strategy": r["strategy"],
                "params": r.get("params", {}),
                "total_return": r["total_return"],
                "benchmark_return": r["benchmark_return"],
                "excess_return": r["excess_return"],
                "sharpe_ratio": r["sharpe_ratio"],
                "max_drawdown": r["max_drawdown"],
                "win_rate": r["win_rate"],
                "trades": r["total_trades"],
                "composite_score": r["composite_score"],
            }
            for i, r in enumerate(results)
        ],
        "best_strategy": results[0]["strategy"],
        "verdict": _strategy_verdict(results[0]),
    }


def _regime_analysis(df: pd.DataFrame, best_strategy: str = "ma_cross",
                     best_params: dict = None) -> dict:
    """划分牛熊震荡，用最优策略在不同行情下验证"""
    close = df["close"].astype(float)
    best_params = best_params or {}

    regimes = _classify_regimes(close)
    if not regimes:
        return {"error": "数据不足以划分行情"}

    regime_results = []
    for regime in regimes:
        mask = (df["date"] >= regime["start"]) & (df["date"] <= regime["end"])
        segment = df[mask]

        if len(segment) < 20:
            continue

        # 用最优策略
        cls = STRATEGY_REGISTRY.get(best_strategy)
        if cls is None:
            continue
        strategy = cls(**best_params)
        engine = BacktestEngine(segment, initial_capital=100_000)
        try:
            result = engine.run(strategy)
            m = result["metrics"]
            regime_results.append({
                "regime": regime["type"],
                "label": f"{regime['start']}~{regime['end']} ({regime['change']:+.1f}%)",
                "days": len(segment),
                "strategy_return": m["total_return"],
                "benchmark_return": m["benchmark_return"],
                "excess_return": m["excess_return"],
                "trades": m["total_trades"],
            })
        except Exception:
            continue

    if not regime_results:
        return {"regimes": regimes, "message": "segments too short for backtesting"}

    # 统计
    bull_results = [r for r in regime_results if r["regime"] == "bull"]
    bear_results = [r for r in regime_results if r["regime"] == "bear"]
    sideways_results = [r for r in regime_results if r["regime"] == "sideways"]

    return {
        "segments": regime_results,
        "summary": {
            "牛市": f"均超额 {_avg(bull_results, 'excess_return'):+.1f}%" if bull_results else "无",
            "熊市": f"均超额 {_avg(bear_results, 'excess_return'):+.1f}%" if bear_results else "无",
            "震荡": f"均超额 {_avg(sideways_results, 'excess_return'):+.1f}%" if sideways_results else "无",
            "best_regime": _best_regime(regime_results),
        },
    }


def _rolling_window(df: pd.DataFrame, best_strategy: str = "ma_cross",
                    best_params: dict = None, window_months: int = 0,
                    step_months: int = 0) -> dict:
    """滚动窗口验证：根据数据长度自适应窗口大小"""
    close = df["close"].astype(float)
    best_params = best_params or {}

    total_months = len(close) / 21  # 约21个交易日/月

    # 自适应窗口：数据越长窗口越大
    if total_months >= 24:
        window_months, step_months = 12, 3
    elif total_months >= 9:
        window_months, step_months = 3, 1
    elif total_months >= 2.5:
        window_months, step_months = 2, 0.5
    elif total_months >= 1.0:
        window_months, step_months = 1, 0.5
    else:
        return {"error": f"数据仅{total_months:.1f}个月，不足以做滚动验证（至少需要1个月）"}

    window = int(window_months * 21)
    step = int(step_months * 21)

    if len(close) < window:
        return {"error": f"数据不足以切出{window_months}个月的窗口"}

    # 使用最优策略
    cls = STRATEGY_REGISTRY.get(best_strategy)
    if cls is None:
        return {"error": f"未知策略: {best_strategy}"}

    windows = []
    start_idx = 0
    while start_idx + window <= len(close):
        segment = df.iloc[start_idx:start_idx + window]
        start_date = segment.iloc[0]["date"]
        end_date = segment.iloc[-1]["date"]
        segment_return = (float(segment.iloc[-1]["close"]) / float(segment.iloc[0]["close"]) - 1) * 100

        # 跑最优策略
        strategy = cls(**best_params)
        engine = BacktestEngine(segment, initial_capital=100_000)
        try:
            result = engine.run(strategy)
            m = result["metrics"]
            windows.append({
                "period": f"{start_date}~{end_date}",
                "strategy_return": m["total_return"],
                "benchmark_return": round(segment_return, 2),
                "excess_return": m["excess_return"],
                "sharpe": m["sharpe_ratio"],
                "max_dd": m["max_drawdown"],
                "trades": m["total_trades"],
                "profitable": m["total_return"] > 0,
                "beat_benchmark": m["excess_return"] > 0,
            })
        except Exception:
            pass

        start_idx += step

    if not windows:
        return {"error": "无法运行滚动窗口"}

    profitable_count = sum(1 for w in windows if w["profitable"])
    beat_count = sum(1 for w in windows if w["beat_benchmark"])

    return {
        "windows": windows,
        "summary": {
            "total_windows": len(windows),
            "profitable_windows": f"{profitable_count}/{len(windows)} ({profitable_count/len(windows)*100:.0f}%)",
            "beat_benchmark": f"{beat_count}/{len(windows)} ({beat_count/len(windows)*100:.0f}%)",
            "avg_excess": round(_avg(windows, "excess_return"), 2),
            "stable": "✅ 稳定" if profitable_count >= len(windows) * 0.6 else "⚠️ 不稳定，慎用",
        },
    }


def _sensitivity_test(df: pd.DataFrame, best_strategy: str = "ma_cross") -> dict:
    """参数敏感性：对最优策略调参，看结果波动大不大"""
    cls = STRATEGY_REGISTRY.get(best_strategy)
    if cls is None:
        return {"error": f"未知策略: {best_strategy}"}

    default_params = cls.default_params()
    results = []
    strategy_label = best_strategy

    if best_strategy == "ma_cross":
        # MA均线：排列组合快慢线
        for fast in [3, 5, 10, 15]:
            for slow in [10, 20, 30, 50, 60]:
                if fast >= slow:
                    continue
                s = cls(fast=fast, slow=slow)
                engine = BacktestEngine(df, initial_capital=100_000)
                try:
                    r = engine.run(s)
                    m = r["metrics"]
                    results.append({
                        "params": f"MA{fast}/{slow}", "total_return": m["total_return"],
                        "excess_return": m["excess_return"], "sharpe": m["sharpe_ratio"],
                        "max_dd": m["max_drawdown"],
                    })
                except Exception:
                    continue

    elif best_strategy == "macd_signal":
        for fast in [8, 12, 16]:
            for slow in [20, 26, 32]:
                for sig in [7, 9, 12]:
                    if fast >= slow:
                        continue
                    s = cls(fast=fast, slow=slow, signal=sig)
                    engine = BacktestEngine(df, initial_capital=100_000)
                    try:
                        r = engine.run(s)
                        m = r["metrics"]
                        results.append({
                            "params": f"MACD({fast},{slow},{sig})",
                            "total_return": m["total_return"],
                            "excess_return": m["excess_return"],
                            "sharpe": m["sharpe_ratio"], "max_dd": m["max_drawdown"],
                        })
                    except Exception:
                        continue

    elif best_strategy == "rsi_mean_rev":
        for period in [7, 14, 21]:
            for oversold in [20, 25, 30, 35]:
                for overbought in [65, 70, 75, 80]:
                    if oversold >= overbought:
                        continue
                    s = cls(period=period, oversold=oversold, overbought=overbought)
                    engine = BacktestEngine(df, initial_capital=100_000)
                    try:
                        r = engine.run(s)
                        m = r["metrics"]
                        results.append({
                            "params": f"RSI({period},{oversold}/{overbought})",
                            "total_return": m["total_return"],
                            "excess_return": m["excess_return"],
                            "sharpe": m["sharpe_ratio"], "max_dd": m["max_drawdown"],
                        })
                    except Exception:
                        continue

    elif best_strategy in ("boll_break", "boll_mean_rev"):
        for period in [10, 20, 30]:
            for std in [1.5, 2.0, 2.5]:
                s = cls(period=period, std=std)
                engine = BacktestEngine(df, initial_capital=100_000)
                try:
                    r = engine.run(s)
                    m = r["metrics"]
                    results.append({
                        "params": f"BB({period},{std})",
                        "total_return": m["total_return"],
                        "excess_return": m["excess_return"],
                        "sharpe": m["sharpe_ratio"], "max_dd": m["max_drawdown"],
                    })
                except Exception:
                    continue

    elif best_strategy == "turtle_channel":
        for entry in [10, 20, 30, 55]:
            for exit_p in [5, 10, 15, 20]:
                if exit_p >= entry:
                    continue
                s = cls(entry=entry, exit_period=exit_p)
                engine = BacktestEngine(df, initial_capital=100_000)
                try:
                    r = engine.run(s)
                    m = r["metrics"]
                    results.append({
                        "params": f"Turtle({entry}/{exit_p})",
                        "total_return": m["total_return"],
                        "excess_return": m["excess_return"],
                        "sharpe": m["sharpe_ratio"], "max_dd": m["max_drawdown"],
                    })
                except Exception:
                    continue

    elif best_strategy == "triple_screen":
        for fast in [3, 5, 10]:
            for mid in [10, 20, 30]:
                for sl in [40, 60, 80]:
                    if fast >= mid or mid >= sl:
                        continue
                    s = cls(fast=fast, mid=mid, slow=sl)
                    engine = BacktestEngine(df, initial_capital=100_000)
                    try:
                        r = engine.run(s)
                        m = r["metrics"]
                        results.append({
                            "params": f"Triple({fast},{mid},{sl})",
                            "total_return": m["total_return"],
                            "excess_return": m["excess_return"],
                            "sharpe": m["sharpe_ratio"], "max_dd": m["max_drawdown"],
                        })
                    except Exception:
                        continue
    else:
        return {"error": f"暂不支持 {best_strategy} 的参数敏感性测试"}

    if not results:
        return {"error": "无法运行敏感性测试"}

    returns = [r["excess_return"] for r in results]
    return {
        "strategy": best_strategy,
        "strategy_label": strategy_label,
        "params_tested": len(results),
        "best_param": max(results, key=lambda x: x["excess_return"]),
        "worst_param": min(results, key=lambda x: x["excess_return"]),
        "mean_excess": round(np.mean(returns), 2),
        "std_excess": round(np.std(returns), 2),
        "stability": (
            "✅ 稳定：不同参数结果差别不大，用默认参数就行"
            if np.std(returns) < 15
            else "⚠️ 敏感：参数选对选错差别很大，需要仔细调参"
        ),
        "all_results": sorted(results, key=lambda x: x["excess_return"], reverse=True)[:6],
    }


# ── 辅助函数 ──

def _classify_regimes(close: pd.Series) -> list[dict]:
    """简单划分牛熊震荡行情"""
    ma60 = close.rolling(60).mean()
    regimes = []
    current_type = None
    current_start = None
    current_start_price = None

    for i in range(120, len(close)):
        price = close.iloc[i]
        ma = ma60.iloc[i]

        # 用 20 日涨跌幅分类
        if i >= 20:
            pct_20d = (price / close.iloc[i - 20] - 1) * 100
        else:
            pct_20d = 0

        if pct_20d > 8:
            rtype = "bull"
        elif pct_20d < -8:
            rtype = "bear"
        else:
            rtype = "sideways"

        if rtype != current_type:
            if current_type and current_start and current_start_price:
                change_pct = (price / current_start_price - 1) * 100
                # 只记显著性行情段（绝对值>5%）
                if abs(change_pct) > 5:
                    regimes.append({
                        "type": current_type,
                        "start": str(current_start),
                        "end": str(close.index[i]),
                        "change": round(change_pct, 1),
                    })
            current_type = rtype
            current_start = close.index[i]
            current_start_price = price

    # 最后一段
    if current_type and current_start and current_start_price:
        change_pct = (close.iloc[-1] / current_start_price - 1) * 100
        if abs(change_pct) > 5:
            regimes.append({
                "type": current_type,
                "start": str(current_start),
                "end": str(close.index[-1]),
                "change": round(change_pct, 1),
            })

    return regimes[:5]  # 最多取5段


def _avg(lst: list, key: str) -> float:
    vals = [x[key] for x in lst if key in x and x[key] is not None]
    return float(np.mean(vals)) if vals else 0


def _best_regime(results: list) -> str:
    regimes = {}
    for r in results:
        t = r["regime"]
        if t not in regimes or r["excess_return"] > regimes[t]["excess_return"]:
            regimes[t] = r
    if not regimes:
        return "数据不足"
    best = max(regimes.values(), key=lambda x: x["excess_return"])
    label = {"bull": "🐂 牛市", "bear": "🐻 熊市", "sideways": "📊 震荡市"}
    return f"{label.get(best['regime'], best['regime'])}表现最好 (超额+{best['excess_return']:.1f}%)"


def _strategy_verdict(best: dict) -> str:
    excess = best.get("excess_return", 0)
    sharpe = best.get("sharpe_ratio", 0)
    trades = best.get("trades", 0)

    if excess > 20 and sharpe > 1:
        return "策略显著优于持有，且风险可控，推荐使用"
    if excess > 0:
        return f"策略略优于持有（超额+{excess:.1f}%），但优势有限"
    if trades == 0:
        return "策略未触发交易，可能参数不合适或数据不足"
    return f"策略未跑赢持有不动（超额{excess:.1f}%），建议换策略或买指数"
