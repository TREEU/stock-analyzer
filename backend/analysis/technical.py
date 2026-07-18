"""技术指标计算模块

纯 pandas/numpy 实现常用技术指标，输出适合前端图表的 JSON 格式。
"""

import pandas as pd
import numpy as np


def compute_indicators(df: pd.DataFrame) -> dict:
    """
    计算所有技术指标。

    Args:
        df: 包含 [date, open, high, low, close, volume] 的 DataFrame

    Returns:
        { data: [...], latest_signals: {...} }
    """
    if df.empty or len(df) < 5:
        return {"data": [], "latest_signals": {}}

    close = df["close"].astype(float)
    high = df["high"].astype(float)
    low = df["low"].astype(float)
    volume = df["volume"].astype(float)

    result_df = pd.DataFrame(index=df.index)
    result_df["date"] = df["date"]

    # ── 移动平均线 ──
    for period in [5, 10, 20, 60, 120, 250]:
        if len(close) >= period:
            result_df[f"ma{period}"] = close.rolling(window=period).mean()
        else:
            result_df[f"ma{period}"] = np.nan

    # ── MACD (EMA实现) ──
    if len(close) >= 26:
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()
        hist = 2 * (dif - dea)
        result_df["macd_dif"] = dif
        result_df["macd_dea"] = dea
        result_df["macd_hist"] = hist

    # ── RSI (EMA平滑) ──
    if len(close) >= 14:
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.ewm(span=14, adjust=False).mean()
        avg_loss = loss.ewm(span=14, adjust=False).mean()
        rs = avg_gain / avg_loss.replace(0, np.nan)
        result_df["rsi"] = 100 - (100 / (1 + rs))

    # ── KDJ (随机指标) ──
    if len(close) >= 9:
        low_n = low.rolling(window=9).min()
        high_n = high.rolling(window=9).max()
        rsv = ((close - low_n) / (high_n - low_n).replace(0, np.nan)) * 100
        # 用 EMA 平滑 K 和 D
        k = rsv.ewm(alpha=1/3, adjust=False).mean()  # 3日平滑
        d = k.ewm(alpha=1/3, adjust=False).mean()
        j = 3 * k - 2 * d
        result_df["kdj_k"] = k
        result_df["kdj_d"] = d
        result_df["kdj_j"] = j

    # ── Bollinger Bands ──
    if len(close) >= 20:
        mid = close.rolling(window=20).mean()
        std = close.rolling(window=20).std()
        result_df["boll_upper"] = mid + 2 * std
        result_df["boll_mid"] = mid
        result_df["boll_lower"] = mid - 2 * std

    # ── 成交量均线 ──
    if len(volume) >= 5:
        result_df["vol_ma5"] = volume.rolling(5).mean()
    if len(volume) >= 20:
        result_df["vol_ma20"] = volume.rolling(20).mean()

    # ── ATR (平均真实波幅) ──
    if len(close) >= 14:
        tr = pd.concat([
            (high - low),
            (high - close.shift(1)).abs(),
            (low - close.shift(1)).abs(),
        ], axis=1).max(axis=1)
        result_df["atr14"] = tr.ewm(span=14, adjust=False).mean()

    # ── 生成信号摘要 ──
    latest_signals = _generate_signals(result_df, close)

    # ── 转为 JSON 友好格式 ──
    data = result_df.where(result_df.notna(), None).to_dict(orient="records")

    return {
        "data": data,
        "latest_signals": latest_signals,
    }


def _generate_signals(df: pd.DataFrame, close: pd.Series) -> dict:
    """根据最新指标值生成交易信号摘要"""
    latest = df.iloc[-1] if len(df) > 0 else {}
    prev = df.iloc[-2] if len(df) > 1 else {}

    signals = {
        "latest_close": round(float(close.iloc[-1]), 2) if len(close) > 0 else None,
        "ma_trend": _ma_trend(df),
        "macd_signal": _macd_signal(latest, prev),
        "rsi_signal": _rsi_signal(latest),
        "kdj_signal": _kdj_signal(latest),
        "boll_signal": _boll_signal(latest, close),
    }
    return signals


def _ma_trend(df: pd.DataFrame) -> str:
    """判断均线趋势"""
    try:
        ma5 = df["ma5"].dropna()
        ma20 = df["ma20"].dropna()
        ma60 = df["ma60"].dropna()

        if len(ma5) < 2 or len(ma20) < 2:
            return "数据不足"

        latest_ma5, prev_ma5 = ma5.iloc[-1], ma5.iloc[-2]
        latest_ma20, prev_ma20 = ma20.iloc[-1], ma20.iloc[-2]
        latest_ma60 = ma60.iloc[-1] if len(ma60) > 0 else None

        # 多头排列
        if latest_ma5 > latest_ma20:
            if latest_ma60 is not None and latest_ma20 > latest_ma60:
                return "多头排列（强势）"
            return "短期多头"

        # 空头排列
        if latest_ma60 is not None and latest_ma5 < latest_ma20 < latest_ma60:
            return "空头排列（弱势）"
        if latest_ma5 < latest_ma20:
            return "短期空头"

        return "均线缠绕（震荡）"
    except Exception:
        return "计算异常"


def _macd_signal(latest, prev) -> str:
    """MACD 信号判断"""
    dif = latest.get("macd_dif")
    dea = latest.get("macd_dea")
    hist = latest.get("macd_hist")

    prev_dif = prev.get("macd_dif") if prev is not None else None
    prev_dea = prev.get("macd_dea") if prev is not None else None

    if dif is None or dea is None:
        return "数据不足"

    if prev_dif is not None and prev_dea is not None:
        # 金叉：DIF 上穿 DEA
        if prev_dif <= prev_dea and dif > dea:
            return "MACD金叉（看涨）"
        # 死叉：DIF 下穿 DEA
        if prev_dif >= prev_dea and dif < dea:
            return "MACD死叉（看跌）"

    if hist is not None:
        if hist > 0:
            return "MACD红柱（多头）" if hist > (prev.get("macd_hist") or 0) else "MACD红柱缩短（警示）"
        else:
            return "MACD绿柱（空头）" if hist < (prev.get("macd_hist") or 0) else "MACD绿柱缩短（好转）"

    return "MACD震荡"


def _rsi_signal(latest) -> str:
    """RSI 信号判断"""
    rsi = latest.get("rsi")
    if rsi is None or pd.isna(rsi):
        return "数据不足"
    if rsi > 80:
        return f"RSI={rsi:.1f} 严重超买"
    if rsi > 70:
        return f"RSI={rsi:.1f} 超买区域"
    if rsi < 20:
        return f"RSI={rsi:.1f} 严重超卖"
    if rsi < 30:
        return f"RSI={rsi:.1f} 超卖区域"
    if 40 <= rsi <= 60:
        return f"RSI={rsi:.1f} 中性区域"
    return f"RSI={rsi:.1f}"


def _kdj_signal(latest) -> str:
    """KDJ 信号判断"""
    k = latest.get("kdj_k")
    d = latest.get("kdj_d")
    j = latest.get("kdj_j")

    if k is None or d is None or pd.isna(k) or pd.isna(d):
        return "数据不足"

    if k < 20 and d < 20:
        return "KDJ超卖区域"
    if k > 80 and d > 80:
        return "KDJ超买区域"
    if k > d:
        return "KDJ多头（K>D）"
    return "KDJ空头（K<D）"


def _boll_signal(latest, close: pd.Series) -> str:
    """Bollinger Band 信号判断"""
    upper = latest.get("boll_upper")
    mid = latest.get("boll_mid")
    lower = latest.get("boll_lower")
    price = close.iloc[-1] if len(close) > 0 else None

    if upper is None or lower is None or price is None:
        return "数据不足"

    bandwidth = (upper - lower) / mid if mid and mid > 0 else 0

    if price >= upper * 0.99:
        return "触及上轨（压力位）"
    if price <= lower * 1.01:
        return "触及下轨（支撑位）"
    if price > mid:
        return "布林带强势区" if bandwidth > 0.15 else "布林带收窄（变盘预警）"
    return "布林带弱势区" if bandwidth > 0.15 else "布林带收窄（变盘预警）"
