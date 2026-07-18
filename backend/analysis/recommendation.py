"""操作建议引擎

基于技术面、估值、风险四个维度加权评分，
生成买入/持有/卖出信号、仓位建议、止盈止损价。
"""
from __future__ import annotations

from backend.config import SCORE_WEIGHTS, MIN_POSITION_PCT, MAX_POSITION_PCT


def generate_recommendation(indicators: dict, valuation: dict, risk: dict,
                            backtest_results: dict | None = None) -> dict:
    """
    综合四维度评分，生成操作建议。

    Args:
        indicators: 技术指标结果
        valuation: 估值分析结果
        risk: 风险分析结果
        backtest_results: 可选的回测结果

    Returns:
        { total_score, signal, confidence, position_pct, reasons, risks, ... }
    """
    reasons = []
    risks_list = []

    # ── 1. 趋势评分 (0-25) ──
    trend_score, trend_reasons, trend_risks = _score_trend(indicators)
    reasons.extend(trend_reasons)
    risks_list.extend(trend_risks)

    # ── 2. 动量评分 (0-25) ──
    momentum_score, mom_reasons, mom_risks = _score_momentum(indicators)
    reasons.extend(mom_reasons)
    risks_list.extend(mom_risks)

    # ── 3. 估值评分 (0-25) ──
    valuation_score, val_reasons, val_risks = _score_valuation(valuation)
    reasons.extend(val_reasons)
    risks_list.extend(val_risks)

    # ── 4. 风险评分 (0-25) ──
    risk_score, risk_reasons, risk_risks = _score_risk(risk)
    reasons.extend(risk_reasons)
    risks_list.extend(risk_risks)

    # ── 综合 ──
    total_score = trend_score + momentum_score + valuation_score + risk_score

    signal, confidence = _determine_signal(total_score)
    position_pct = _calc_position_pct(total_score, risk)
    stop_loss, take_profit = _calc_stop_take_profit(indicators, risk)

    return {
        "total_score": round(total_score, 1),
        "signal": signal,
        "confidence": confidence,
        "position_pct": round(position_pct, 1),
        "reasons": reasons[:8],
        "risks": risks_list[:6],
        "suggested_stop_loss": stop_loss,
        "suggested_take_profit": take_profit,
        "latest_price": indicators.get("latest_signals", {}).get("latest_close"),
        "trend_score": round(trend_score, 1),
        "momentum_score": round(momentum_score, 1),
        "valuation_score": round(valuation_score, 1),
        "risk_score": round(risk_score, 1),
    }


# ── 各维度评分函数 ──

def _score_trend(indicators: dict) -> tuple[float, list, list]:
    """趋势维度评分"""
    signals = indicators.get("latest_signals", {})
    ma_trend = signals.get("ma_trend", "")
    macd_signal = signals.get("macd_signal", "")

    score = 12.5  # 基准分
    reasons = []
    risks = []

    if "多头排列" in ma_trend:
        score += 10
        reasons.append("均线多头排列，趋势强劲")
    elif "短期多头" in ma_trend:
        score += 5
        reasons.append("短期均线走强")
    elif "空头排列" in ma_trend:
        score -= 8
        risks.append("均线空头排列，趋势偏弱")
    elif "短期空头" in ma_trend:
        score -= 4
        risks.append("短期均线走弱")
    else:
        reasons.append("均线缠绕，方向不明确")

    if "金叉" in macd_signal:
        score += 8
        reasons.append(macd_signal)
    elif "死叉" in macd_signal:
        score -= 6
        risks.append(macd_signal)
    elif "红柱" in macd_signal:
        score += 3
    elif "绿柱" in macd_signal:
        score -= 2

    return max(0, min(25, score)), reasons, risks


def _score_momentum(indicators: dict) -> tuple[float, list, list]:
    """动量维度评分"""
    signals = indicators.get("latest_signals", {})
    rsi_signal = signals.get("rsi_signal", "")
    kdj_signal = signals.get("kdj_signal", "")
    boll_signal = signals.get("boll_signal", "")

    score = 12.5
    reasons = []
    risks = []

    # RSI
    if "超卖" in rsi_signal:
        score += 6
        reasons.append(rsi_signal + "（潜在反弹机会）")
    elif "超买" in rsi_signal:
        score -= 5
        risks.append(rsi_signal + "（回调风险）")
    elif "中性" in rsi_signal:
        score += 3
        reasons.append(rsi_signal)

    # KDJ
    if "超卖" in kdj_signal:
        score += 4
        reasons.append(kdj_signal)
    elif "超买" in kdj_signal:
        score -= 3
        risks.append(kdj_signal)
    elif "多头" in kdj_signal:
        score += 2

    # Bollinger
    if "下轨" in boll_signal or "支撑" in boll_signal:
        score += 4
        reasons.append(boll_signal)
    elif "上轨" in boll_signal or "压力" in boll_signal:
        score -= 3
        risks.append(boll_signal)
    elif "收窄" in boll_signal:
        reasons.append(boll_signal)

    return max(0, min(25, score)), reasons, risks


def _score_valuation(valuation: dict) -> tuple[float, list, list]:
    """估值维度评分"""
    assessment = valuation.get("assessment", "")
    pe = valuation.get("pe_ttm") or 0
    pb = valuation.get("pb") or 0

    score = 12.5
    reasons = []
    risks = []

    if "显著低估" in assessment:
        score += 12
        reasons.append(f"估值显著低估（PE={pe}, PB={pb}）")
    elif "偏低" in assessment:
        score += 8
        reasons.append(f"估值偏低（PE={pe}, PB={pb}）")
    elif "合理" in assessment:
        score += 3
        reasons.append(f"估值合理（PE={pe}, PB={pb}）")
    elif "显著高估" in assessment:
        score -= 10
        risks.append(f"估值显著偏高（PE={pe}, PB={pb}）")
    elif "偏高" in assessment:
        score -= 5
        risks.append(f"估值偏高（PE={pe}, PB={pb}）")
    else:
        reasons.append("估值数据参考有限")

    # PE 分位
    pe_pct = valuation.get("pe_percentile")
    if pe_pct is not None:
        if pe_pct < 20:
            reasons.append(f"PE处于历史{pe_pct:.0f}%分位 — 相对便宜")
        elif pe_pct > 80:
            risks.append(f"PE处于历史{pe_pct:.0f}%分位 — 相对昂贵")

    return max(0, min(25, score)), reasons, risks


def _score_risk(risk: dict) -> tuple[float, list, list]:
    """风险维度评分"""
    sharpe = risk.get("sharpe_ratio", 0)
    max_dd = risk.get("max_drawdown", 0)
    vol = risk.get("annual_volatility", 0)
    beta = risk.get("beta")

    score = 12.5
    reasons = []
    risks = []

    if sharpe > 1.5:
        score += 8
        reasons.append(f"Sharpe比率={sharpe:.2f}，风险调整收益优秀")
    elif sharpe > 0.8:
        score += 4
        reasons.append(f"Sharpe比率={sharpe:.2f}，风险调整收益良好")
    elif sharpe > 0:
        score += 1
    elif sharpe < 0:
        score -= 6
        risks.append(f"Sharpe比率={sharpe:.2f}，风险调整收益为负")

    if abs(max_dd) < 15:
        score += 4
        reasons.append(f"最大回撤仅{abs(max_dd):.1f}%，风控良好")
    elif abs(max_dd) > 35:
        score -= 5
        risks.append(f"最大回撤{abs(max_dd):.1f}%，波动较大")

    if vol < 25:
        score += 3
    elif vol > 45:
        score -= 3
        risks.append(f"年化波动率{vol:.1f}%，波动较大")

    if beta is not None:
        if 0.8 <= beta <= 1.2:
            reasons.append(f"Beta={beta:.2f}，与市场同步")
        elif beta > 1.5:
            risks.append(f"Beta={beta:.2f}，波动显著大于市场")

    return max(0, min(25, score)), reasons, risks


# ── 辅助决策函数 ──

def _determine_signal(total_score: float) -> tuple[str, str]:
    """根据总分确定信号和置信度"""
    if total_score >= 75:
        return "buy", "high"
    elif total_score >= 60:
        return "buy", "medium"
    elif total_score >= 45:
        return "hold", "medium"
    elif total_score >= 30:
        return "hold", "low"
    else:
        return "sell", "medium" if total_score < 20 else "low"


def _calc_position_pct(total_score: float, risk: dict) -> float:
    """根据评分和风险计算建议仓位比例"""
    base = total_score / 100  # 0-1
    vol = risk.get("annual_volatility", 30)
    vol_factor = 25 / max(vol, 10)  # 波动率越低仓位越高
    position = base * MAX_POSITION_PCT * vol_factor
    return max(MIN_POSITION_PCT, min(MAX_POSITION_PCT, position))


def _calc_stop_take_profit(indicators: dict, risk: dict) -> tuple[float | None, float | None]:
    """计算建议止盈止损价"""
    latest_price = indicators.get("latest_signals", {}).get("latest_close")
    atr = None

    # 尝试从指标数据中取最新 ATR
    data = indicators.get("data", [])
    if data:
        last = data[-1]
        atr = last.get("atr14")

    if latest_price is None:
        return None, None

    # 止损：2倍 ATR 或 8%
    if atr and atr > 0:
        stop_loss = round(latest_price - 2 * atr, 2)
    else:
        stop_loss = round(latest_price * 0.92, 2)

    # 止盈：3倍 ATR 或 20%
    if atr and atr > 0:
        take_profit = round(latest_price + 3 * atr, 2)
    else:
        take_profit = round(latest_price * 1.20, 2)

    return stop_loss, take_profit
