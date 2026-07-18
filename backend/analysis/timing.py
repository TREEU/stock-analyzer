"""买卖时机预测引擎

基于技术指标给出具体的买入价、卖出价、操作建议。
组合了支撑/压力位分析、均线位置、回测策略匹配。
"""
from __future__ import annotations

import pandas as pd
import numpy as np

from backend.data.fetcher import fetch_daily_price
from backend.analysis.technical import compute_indicators


def analyze_timing(code: str, cost_price: float = 0) -> dict:
    """
    对单只股票做买卖时机分析。

    Args:
        code: 股票代码
        cost_price: 用户持仓成本价（0 表示无持仓）

    Returns:
        {
            current_price, pnl_pct,
            buy_zone: {low, high},      # 买入区间
            sell_zone: {low, high},     # 卖出区间
            support_levels: [...],      # 支撑位
            resistance_levels: [...],   # 压力位
            signal,                     # 操作建议
            reasons: [...],             # 理由
            risks: [...],               # 风险
            confidence,                 # 置信度
        }
    """
    # 获取价格数据
    df = fetch_daily_price(code)
    if df is None or df.empty:
        return {"error": "无法获取数据"}

    close = df["close"].astype(float)
    current_price = float(close.iloc[-1])

    # 计算技术指标
    indicators = compute_indicators(df)
    signals = indicators.get("latest_signals", {})
    ind_data = indicators.get("data", [])

    # ── 计算支撑/压力位 ──
    supports = _find_supports(df, current_price)
    resistances = _find_resistances(df, current_price)

    # ── 计算买入区间 ──
    buy_zone = _calc_buy_zone(df, current_price, supports)

    # ── 计算卖出区间 ──
    sell_zone = _calc_sell_zone(df, current_price, resistances)

    # ── 持持仓盈亏 ──
    pnl_pct = 0.0
    if cost_price > 0:
        pnl_pct = (current_price - cost_price) / cost_price * 100

    # ── 综合操作建议 ──
    signal, confidence, reasons, risks = _make_advice(
        current_price, cost_price, pnl_pct,
        signals, supports, resistances,
        buy_zone, sell_zone,
    )

    # ── ATR 止损止盈 ──
    atr = None
    if ind_data:
        last = ind_data[-1]
        atr = last.get("atr14")

    stop_loss = round(current_price - 2 * atr, 2) if atr else round(current_price * 0.92, 2)
    take_profit = round(current_price + 3 * atr, 2) if atr else round(current_price * 1.20, 2)

    return {
        "code": code,
        "current_price": round(current_price, 3),
        "cost_price": round(cost_price, 3) if cost_price else None,
        "pnl_pct": round(pnl_pct, 2),
        "buy_zone": buy_zone,
        "sell_zone": sell_zone,
        "support_levels": supports[:3],
        "resistance_levels": resistances[:3],
        "signal": signal,
        "confidence": confidence,
        "reasons": reasons,
        "risks": risks,
        "stop_loss": stop_loss,
        "take_profit": take_profit,
        "ma_trend": signals.get("ma_trend", ""),
        "macd_signal": signals.get("macd_signal", ""),
        "rsi_signal": signals.get("rsi_signal", ""),
        "boll_signal": signals.get("boll_signal", ""),
    }


def _find_supports(df: pd.DataFrame, current_price: float) -> list[dict]:
    """找出支撑位"""
    close = df["close"].astype(float)
    low = df["low"].astype(float)
    supports = []

    # MA20 / MA60 支撑
    for p, label in [(20, "MA20"), (60, "MA60"), (120, "MA120")]:
        ma = close.rolling(p).mean().iloc[-1]
        if pd.notna(ma) and ma < current_price:
            supports.append({"level": round(float(ma), 2), "type": label})

    # 布林下轨
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_low = bb_mid - 2 * bb_std
    if pd.notna(bb_low.iloc[-1]) and bb_low.iloc[-1] < current_price:
        supports.append({"level": round(float(bb_low.iloc[-1]), 2), "type": "布林下轨"})

    # 近期最低价
    recent_low = low.tail(20).min()
    if recent_low < current_price:
        supports.append({"level": round(float(recent_low), 2), "type": "20日最低"})

    # 按离当前价距离排序（最近的支撑优先）
    supports.sort(key=lambda x: current_price - x["level"])
    return supports


def _find_resistances(df: pd.DataFrame, current_price: float) -> list[dict]:
    """找出压力位"""
    close = df["close"].astype(float)
    high = df["high"].astype(float)
    resistances = []

    # MA20 / MA60 压力
    for p, label in [(20, "MA20"), (60, "MA60"), (120, "MA120")]:
        ma = close.rolling(p).mean().iloc[-1]
        if pd.notna(ma) and ma > current_price:
            resistances.append({"level": round(float(ma), 2), "type": label})

    # 布林上轨
    bb_mid = close.rolling(20).mean()
    bb_std = close.rolling(20).std()
    bb_high = bb_mid + 2 * bb_std
    if pd.notna(bb_high.iloc[-1]) and bb_high.iloc[-1] > current_price:
        resistances.append({"level": round(float(bb_high.iloc[-1]), 2), "type": "布林上轨"})

    # 近期最高价
    recent_high = high.tail(20).max()
    if recent_high > current_price:
        resistances.append({"level": round(float(recent_high), 2), "type": "20日最高"})

    # 前高（60日）
    high_60 = high.tail(60).max()
    if high_60 > current_price and high_60 not in [r["level"] for r in resistances]:
        resistances.append({"level": round(float(high_60), 2), "type": "60日最高"})

    resistances.sort(key=lambda x: x["level"] - current_price)
    return resistances


def _calc_buy_zone(df, current_price, supports) -> dict:
    """计算建议买入区间"""
    if supports:
        # 最近支撑下方 1%~3% 作为买入区
        nearest = supports[0]["level"]
        return {
            "low": round(nearest * 0.97, 2),
            "high": round(nearest * 1.01, 2),
            "label": f"回调至{supports[0]['type']}(¥{nearest})附近",
        }
    # 无支撑位，用近期回撤幅度估算
    return {
        "low": round(current_price * 0.93, 2),
        "high": round(current_price * 0.97, 2),
        "label": "技术回调区间（-3%~-7%）",
    }


def _calc_sell_zone(df, current_price, resistances) -> dict:
    """计算建议卖出区间"""
    if resistances:
        nearest = resistances[0]["level"]
        return {
            "low": round(nearest * 0.99, 2),
            "high": round(nearest * 1.03, 2),
            "label": f"反弹至{resistances[0]['type']}(¥{nearest})附近",
        }
    return {
        "low": round(current_price * 1.05, 2),
        "high": round(current_price * 1.12, 2),
        "label": "前高突破区间（+5%~+12%）",
    }


def _make_advice(current_price, cost_price, pnl_pct,
                 signals, supports, resistances,
                 buy_zone, sell_zone) -> tuple:
    """综合信号生成操作建议"""
    reasons = []
    risks = []

    # ── 趋势判断 ──
    ma_trend = signals.get("ma_trend", "")
    macd = signals.get("macd_signal", "")
    rsi_sig = signals.get("rsi_signal", "")

    trend_bullish = "多" in ma_trend
    macd_bullish = "金叉" in macd or ("红柱" in macd and "缩短" not in macd)
    rsi_oversold = "超卖" in rsi_sig
    rsi_overbought = "超买" in rsi_sig

    # 打分
    score = 0
    if trend_bullish:
        score += 2
        reasons.append(f"均线{ma_trend}")
    else:
        score -= 1
        risks.append(f"均线{ma_trend}")

    if macd_bullish:
        score += 2
        reasons.append(macd)
    elif "死叉" in macd:
        score -= 2
        risks.append(macd)

    if rsi_oversold:
        score += 1
        reasons.append(rsi_sig + " 潜在反弹机会")
    elif rsi_overbought:
        score -= 1
        risks.append(rsi_sig + " 注意回调")

    # 价格位置
    if supports:
        nearest_support = supports[0]
        dist_to_support = (current_price - nearest_support["level"]) / current_price * 100
        if dist_to_support < 2:
            reasons.append(f"距{nearest_support['type']}仅{dist_to_support:.1f}%，接近支撑")
        elif dist_to_support > 10:
            risks.append(f"距最近支撑{dist_to_support:.0f}%，回调空间大")

    if resistances:
        nearest_resist = resistances[0]
        dist_to_resist = (nearest_resist["level"] - current_price) / current_price * 100
        if dist_to_resist < 2:
            risks.append(f"距{nearest_resist['type']}仅{dist_to_resist:.1f}%，压力临近")
        elif dist_to_resist > 8:
            reasons.append(f"上方空间{dist_to_resist:.0f}%，突破后有较大涨幅空间")

    # 盈亏状态
    if cost_price > 0:
        if pnl_pct > 20:
            score -= 1
            risks.append(f"已盈利{pnl_pct:.0f}%，可考虑分批止盈")
        elif pnl_pct > 10:
            reasons.append(f"盈利{pnl_pct:.0f}%，趋势良好可持有")
        elif pnl_pct < -10:
            score -= 2
            risks.append(f"亏损{abs(pnl_pct):.0f}%，建议评估是否止损")
        elif pnl_pct < -5:
            risks.append(f"浮亏{abs(pnl_pct):.0f}%，关注支撑位")

    # 信号判定
    if score >= 4:
        signal = "buy"
        confidence = "high"
        reasons.insert(0, "多信号共振，建议买入/加仓")
    elif score >= 2:
        signal = "buy"
        confidence = "medium"
        reasons.insert(0, "信号偏多，可逐步建仓")
    elif score >= 0:
        signal = "hold"
        confidence = "medium"
        reasons.insert(0, "信号中性，建议持有观望")
    elif score >= -2:
        signal = "hold"
        confidence = "low"
        reasons.insert(0, "信号偏弱，建议减仓或观望")
    else:
        signal = "sell"
        confidence = "medium"
        reasons.insert(0, "信号偏空，建议卖出/减仓")

    return signal, confidence, reasons[:6], risks[:4]
