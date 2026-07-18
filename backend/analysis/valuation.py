"""估值分析模块

基于 PE_TTM 和 PB 的当前值、历史分位、行业对比 评估估值水平。
"""
from __future__ import annotations

import akshare as ak
import pandas as pd
import numpy as np

from backend.data.fetcher import fetch_index_valuation


def assess_valuation(code: str, stock_info: dict) -> dict:
    """
    评估单只股票的估值水平。

    Returns:
        { pe_ttm, pb, pe_percentile, pb_percentile,
          index_pe, index_pb, index_pe_percentile, assessment }
    """
    pe_ttm = stock_info.get("pe_ttm", 0) or 0
    pb = stock_info.get("pb", 0) or 0

    # 获取历史 PE/PB 分位（5年）
    pe_percentile = _calc_pe_percentile(code)
    pb_percentile = _calc_pb_percentile(code)

    # 获取指数估值参考
    index_val = fetch_index_valuation("沪深300")

    # 综合评估
    assessment = _make_assessment(pe_ttm, pb, pe_percentile, pb_percentile, index_val)

    return {
        "pe_ttm": round(pe_ttm, 2) if pe_ttm else None,
        "pb": round(pb, 2) if pb else None,
        "pe_percentile": round(pe_percentile, 1) if pe_percentile is not None else None,
        "pb_percentile": round(pb_percentile, 1) if pb_percentile is not None else None,
        "index_pe": round(index_val.get("index_pe", 0), 2) if index_val.get("index_pe") else None,
        "index_pb": round(index_val.get("index_pb", 0), 2) if index_val.get("index_pb") else None,
        "index_pe_percentile": index_val.get("index_pe_percentile"),
        "index_pb_percentile": index_val.get("index_pb_percentile"),
        "assessment": assessment,
    }


def _calc_pe_percentile(code: str) -> float | None:
    """计算个股 PE 历史分位（近5年季度数据）"""
    try:
        # 使用 akshare 获取个股财务指标
        df = ak.stock_financial_abstract_ths(symbol=code, indicator="按年度")
        if df is None or df.empty:
            return None

        # 尝试获取 PE 相关列
        pe_cols = [c for c in df.columns if "市盈率" in str(c) or "PE" in str(c).upper()]
        if not pe_cols:
            return None

        pe_values = pd.to_numeric(df[pe_cols[0]], errors="coerce").dropna()
        if len(pe_values) < 4:
            return None

        # 取最近5年数据计算分位
        recent_pe = pe_values.tail(5)
        current_pe = recent_pe.iloc[-1]
        percentile = (recent_pe < current_pe).mean() * 100
        return float(percentile)
    except Exception:
        return None


def _calc_pb_percentile(code: str) -> float | None:
    """计算个股 PB 历史分位"""
    try:
        df = ak.stock_financial_abstract_ths(symbol=code, indicator="按年度")
        if df is None or df.empty:
            return None

        pb_cols = [c for c in df.columns if "市净率" in str(c) or "PB" in str(c).upper()]
        if not pb_cols:
            return None

        pb_values = pd.to_numeric(df[pb_cols[0]], errors="coerce").dropna()
        if len(pb_values) < 4:
            return None

        recent_pb = pb_values.tail(5)
        current_pb = recent_pb.iloc[-1]
        percentile = (recent_pb < current_pb).mean() * 100
        return float(percentile)
    except Exception:
        return None


def _make_assessment(pe: float, pb: float,
                     pe_pct: float | None, pb_pct: float | None,
                     index_val: dict) -> str:
    """综合生成估值评估文字"""

    # 无效估值的处理
    if (pe <= 0 or pe > 500) and (pb <= 0 or pb > 50):
        return "估值数据异常（可能为亏损股）"

    # 综合分位评分
    scores = []

    if pe_pct is not None:
        if pe_pct < 10:
            scores.append(("pe", "significantly_undervalued"))
        elif pe_pct < 25:
            scores.append(("pe", "undervalued"))
        elif pe_pct < 75:
            scores.append(("pe", "fair"))
        elif pe_pct < 90:
            scores.append(("pe", "overvalued"))
        else:
            scores.append(("pe", "significantly_overvalued"))
    else:
        # 用绝对值粗略判断
        if 0 < pe < 15:
            scores.append(("pe", "undervalued"))
        elif 15 <= pe <= 30:
            scores.append(("pe", "fair"))
        elif pe > 30:
            scores.append(("pe", "overvalued"))

    if pb_pct is not None:
        if pb_pct < 10:
            scores.append(("pb", "significantly_undervalued"))
        elif pb_pct < 25:
            scores.append(("pb", "undervalued"))
        elif pb_pct < 75:
            scores.append(("pb", "fair"))
        elif pb_pct < 90:
            scores.append(("pb", "overvalued"))
        else:
            scores.append(("pb", "significantly_overvalued"))
    else:
        if 0 < pb < 1:
            scores.append(("pb", "undervalued"))
        elif 1 <= pb <= 4:
            scores.append(("pb", "fair"))
        elif pb > 4:
            scores.append(("pb", "overvalued"))

    # 汇总评分
    from collections import Counter
    levels = [s[1] for s in scores]
    count = Counter(levels)
    most_common = count.most_common(1)[0][0]

    labels = {
        "significantly_undervalued": "显著低估",
        "undervalued": "估值偏低",
        "fair": "估值合理",
        "overvalued": "估值偏高",
        "significantly_overvalued": "显著高估",
    }
    return labels.get(most_common, "估值合理")
