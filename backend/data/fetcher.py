"""数据获取封装层

使用腾讯 API 获取 A 股日线数据。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

import requests
import akshare as ak
import pandas as pd

from backend.cache import price_cache, spot_cache, valuation_cache
from backend.config import CACHE_TTL


def _normalize_code(code: str) -> str:
    """确保股票代码为 6 位数字字符串"""
    return code.strip().zfill(6)


def _to_date_str(date_obj) -> str:
    """将各种日期输入转为 YYYYMMDD 字符串"""
    if isinstance(date_obj, str):
        return date_obj.replace("-", "")
    if isinstance(date_obj, (datetime, pd.Timestamp)):
        return date_obj.strftime("%Y%m%d")
    return str(date_obj)


def _get_market_code(code: str) -> int:
    """判断股票的市场代码：0=深圳, 1=上海"""
    if code.startswith(("6", "9")):
        return 1  # 上海
    return 0  # 深圳（0/2/3开头）


def _fetch_price_fallback(code: str, start: str, end: str,
                          adjust: str, cache_key: str) -> Optional[pd.DataFrame]:
    """回退方案：尝试用 akshare 获取数据"""
    try:
        df = ak.stock_zh_a_hist(symbol=code, period="daily",
                                start_date=start, end_date=end, adjust=adjust)
        if df is None or df.empty:
            return None
        df = df.rename(columns={
            "日期": "date", "开盘": "open", "收盘": "close",
            "最高": "high", "最低": "low", "成交量": "volume",
            "成交额": "amount", "振幅": "amplitude",
            "涨跌幅": "pct_change", "涨跌额": "change_amount",
            "换手率": "turnover_rate",
        })
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
        numeric_cols = ["open", "close", "high", "low", "volume", "amount",
                        "amplitude", "pct_change", "change_amount", "turnover_rate"]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
        df = df.sort_values("date").reset_index(drop=True)
        price_cache.set(cache_key, df.copy(), CACHE_TTL["price"])
        return df
    except Exception as e:
        print(f"[fallback] also failed: {e}")
        return None


def search_stocks(keyword: str) -> list[dict]:
    """搜索股票（按代码或名称模糊匹配）"""
    if not keyword or len(keyword.strip()) < 2:
        return []

    keyword = keyword.strip()
    cache_key = f"search_{keyword}"

    cached = spot_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        df = _get_stock_list()
        if df is None or df.empty:
            return []

        # 按代码或名称模糊匹配
        mask = (
            df["code"].str.contains(keyword, na=False)
            | df["name"].str.contains(keyword, na=False)
        )
        result = df[mask].head(20)[["code", "name"]].to_dict(orient="records")

        spot_cache.set(cache_key, result, CACHE_TTL["spot"])
        return result
    except Exception:
        return []


def _get_stock_list() -> Optional[pd.DataFrame]:
    """获取全A股票代码名称列表（带缓存）"""
    cached = spot_cache.get("stock_list")
    if cached is not None:
        return cached

    try:
        df = ak.stock_info_a_code_name()
        df = df.rename(columns={"code": "code", "name": "name"})
        df["code"] = df["code"].astype(str).str.zfill(6)
        spot_cache.set("stock_list", df, CACHE_TTL["spot"])
        return df
    except Exception:
        return None


def _get_spot_safe() -> Optional[pd.DataFrame]:
    """安全获取实时行情（带缓存，失败返回 None）"""
    cached = spot_cache.get("spot_all")
    if cached is not None:
        return cached

    try:
        df = ak.stock_zh_a_spot_em()
        df = df.rename(columns={
            "代码": "code", "名称": "name",
            "最新价": "latest_price", "涨跌幅": "pct_change",
            "涨跌额": "change_amount", "成交量": "volume",
            "成交额": "amount", "振幅": "amplitude",
            "换手率": "turnover_rate", "量比": "volume_ratio",
            "市盈率-动态": "pe_ttm", "市净率": "pb",
            "总市值": "market_cap", "流通市值": "float_cap",
            "60日涨跌幅": "pct_change_60d",
            "年初至今涨跌幅": "pct_change_ytd",
        })
        df["code"] = df["code"].astype(str).str.zfill(6)
        spot_cache.set("spot_all", df, CACHE_TTL["spot"])
        return df
    except Exception:
        return None


def fetch_daily_price(
    code: str,
    start: str = "20230101",
    end: str = "",
    adjust: str = "qfq",
) -> Optional[pd.DataFrame]:
    """获取单只股票日线数据（前复权），使用腾讯API"""
    from backend.config import get_default_end_date
    code = _normalize_code(code)
    if not end:
        end = get_default_end_date()
    start = _to_date_str(start)
    end = _to_date_str(end)

    cache_key = f"price_{code}_{start}_{end}_{adjust}"
    cached = price_cache.get(cache_key)
    if cached is not None:
        return cached.copy()

    try:
        # 市场前缀
        if code.startswith(("6", "9")):
            prefix = "sh"
        else:
            prefix = "sz"

        # 复权参数: qfq=前复权, hfq=后复权, '不复权'=空
        fq_map = {"qfq": "qfq", "hfq": "hfq", "": ""}
        fq = fq_map.get(adjust, "qfq")

        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:8]}"

        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {
            "param": f"{prefix}{code},day,{start_fmt},{end_fmt},640,{fq}",
        }

        s = requests.Session()
        s.trust_env = False
        resp = s.get(url, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            return _fetch_price_fallback(code, start, end, adjust, cache_key)

        stock_key = f"{prefix}{code}"
        stock_data = data.get("data", {}).get(stock_key)
        if not stock_data:
            return None

        # 取对应复权数据
        key_map = {"qfq": "qfqday", "hfq": "hfqday", "": "day"}
        day_key = key_map.get(adjust, "qfqday")
        klines = stock_data.get(day_key, [])
        if not klines:
            # 尝试不复权
            klines = stock_data.get("day", [])

        if not klines:
            return None

        # 腾讯格式: [date, open, close, high, low, volume]
        rows = []
        for line in klines:
            rows.append({
                "date": line[0],
                "open": float(line[1]),
                "close": float(line[2]),
                "high": float(line[3]),
                "low": float(line[4]),
                "volume": float(line[5]),
            })

        df = pd.DataFrame(rows)
        df = df.sort_values("date").reset_index(drop=True)

        # 计算涨跌幅、振幅（腾讯数据不含这些）
        df["pct_change"] = (df["close"].pct_change() * 100).round(2)
        df["amplitude"] = ((df["high"] - df["low"]) / df["close"].shift(1) * 100).round(2)
        df["amount"] = None
        df["change_amount"] = (df["close"] - df["close"].shift(1)).round(2)
        df["turnover_rate"] = None

        price_cache.set(cache_key, df.copy(), CACHE_TTL["price"])
        return df
    except Exception as e:
        print(f"[fetch_daily_price] Tencent error for {code}: {e}")
        return _fetch_price_fallback(code, start, end, adjust, cache_key)


def fetch_stock_info(code: str) -> dict:
    """获取单只股票的基本信息（实时数据优先，历史数据兜底）"""
    code = _normalize_code(code)
    result = {
        "code": code,
        "name": "",
        "latest_price": 0,
        "pct_change": 0,
        "pe_ttm": 0,
        "pb": 0,
        "market_cap": 0,
        "turnover_rate": 0,
    }

    # 先尝试获取股票名称
    try:
        stock_list = _get_stock_list()
        if stock_list is not None:
            row = stock_list[stock_list["code"] == code]
            if not row.empty:
                result["name"] = str(row.iloc[0]["name"])
    except Exception:
        pass

    # 尝试实时行情
    try:
        spot = _get_spot_safe()
        if spot is not None:
            row = spot[spot["code"] == code]
            if not row.empty:
                r = row.iloc[0]
                result["name"] = result["name"] or str(r.get("name", ""))
                result["latest_price"] = float(r.get("latest_price", 0) or 0)
                result["pct_change"] = float(r.get("pct_change", 0) or 0)
                result["pe_ttm"] = float(r.get("pe_ttm", 0) or 0)
                result["pb"] = float(r.get("pb", 0) or 0)
                result["market_cap"] = float(r.get("market_cap", 0) or 0)
                result["turnover_rate"] = float(r.get("turnover_rate", 0) or 0)
                return result
    except Exception:
        pass

    # 实时行情不可用时，从历史数据取最新价
    if result["latest_price"] == 0:
        try:
            df = fetch_daily_price(code)
            if df is not None and not df.empty:
                last = df.iloc[-1]
                result["latest_price"] = float(last["close"])
                result["pct_change"] = float(last.get("pct_change", 0) or 0)
                result["turnover_rate"] = float(last.get("turnover_rate", 0) or 0)
        except Exception:
            pass

    return result


def fetch_index_daily(code: str = "sh000001", start: str = "20230101",
                      end: str = "") -> Optional[pd.DataFrame]:
    """获取指数日线数据（用于 Beta 计算），使用腾讯API"""
    from backend.config import get_default_end_date
    start = _to_date_str(start)
    end = _to_date_str(end) if end else get_default_end_date()

    cache_key = f"index_{code}_{start}_{end}"
    cached = price_cache.get(cache_key)
    if cached is not None:
        return cached.copy()

    try:
        start_fmt = f"{start[:4]}-{start[4:6]}-{start[6:8]}"
        end_fmt = f"{end[:4]}-{end[4:6]}-{end[6:8]}"

        url = "https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {"param": f"{code},day,{start_fmt},{end_fmt},640,"}

        s = requests.Session()
        s.trust_env = False
        resp = s.get(url, params=params, timeout=30)
        data = resp.json()

        if data.get("code") != 0:
            return None

        stock_data = data.get("data", {}).get(code)
        if not stock_data:
            return None

        klines = stock_data.get("day", [])
        if not klines:
            return None

        rows = []
        for line in klines:
            rows.append({
                "date": line[0],
                "open": float(line[1]),
                "close": float(line[2]),
                "high": float(line[3]),
                "low": float(line[4]),
                "volume": float(line[5]),
            })

        df = pd.DataFrame(rows)
        df = df.sort_values("date").reset_index(drop=True)

        for col in ["open", "close", "high", "low", "volume"]:
            df[col] = pd.to_numeric(df[col], errors="coerce")

        price_cache.set(cache_key, df.copy(), CACHE_TTL["price"])
        return df
    except Exception as e:
        print(f"[fetch_index_daily] Error: {e}")
        return None


def fetch_index_valuation(index_name: str = "沪深300") -> dict:
    """获取指数 PE/PB 估值分位数据"""
    cache_key = f"index_val_{index_name}"
    cached = valuation_cache.get(cache_key)
    if cached is not None:
        return cached

    try:
        pe_df = ak.stock_index_pe_lg(symbol=index_name)
        pb_df = ak.stock_index_pb_lg(symbol=index_name)

        result = {}
        if pe_df is not None and not pe_df.empty:
            latest_pe = pe_df.iloc[-1]
            pe_values = pd.to_numeric(pe_df["平均市盈率"] if "平均市盈率" in pe_df.columns
                                      else pe_df.iloc[:, 1], errors="coerce").dropna()
            current_pe = float(pe_values.iloc[-1])
            pe_percentile = (pe_values < current_pe).mean() * 100
            result["index_pe"] = current_pe
            result["index_pe_percentile"] = round(pe_percentile, 1)

        if pb_df is not None and not pb_df.empty:
            pb_values = pd.to_numeric(pb_df["平均市净率"] if "平均市净率" in pb_df.columns
                                      else pb_df.iloc[:, 1], errors="coerce").dropna()
            current_pb = float(pb_values.iloc[-1])
            pb_percentile = (pb_values < current_pb).mean() * 100
            result["index_pb"] = current_pb
            result["index_pb_percentile"] = round(pb_percentile, 1)

        valuation_cache.set(cache_key, result, CACHE_TTL["valuation"])
        return result
    except Exception as e:
        print(f"[fetch_index_valuation] Error: {e}")
        return {}
