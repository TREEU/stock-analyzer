"""实时行情和市场数据模块

数据源：新浪财经 + 腾讯财经 API
"""

import requests
import json
from backend.cache import spot_cache
from backend.config import CACHE_TTL


def _get_session():
    s = requests.Session()
    s.trust_env = False
    return s


# ── 实时行情（腾讯源） ──

def get_realtime_quotes(codes: list[str]) -> list[dict]:
    """获取多只股票实时行情"""
    if not codes:
        return []

    cache_key = f"realtime_{','.join(codes)}"
    cached = spot_cache.get(cache_key)
    if cached:
        return cached

    # 加市场前缀
    prefixed = []
    for c in codes:
        c = c.strip().zfill(6)
        prefix = "sh" if c.startswith(("6", "9")) else "sz"
        prefixed.append(f"{prefix}{c}")

    try:
        s = _get_session()
        url = "https://qt.gtimg.cn/q=" + ",".join(prefixed)
        resp = s.get(url, headers={"Referer": "https://finance.qq.com"}, timeout=10)
        resp.encoding = "gbk"

        results = []
        for line in resp.text.strip().split("\n"):
            if not line.strip() or "=" not in line:
                continue
            # 格式: v_sz000001="51~name~code~price~..."
            parts = line.split("=")[1].strip('";').split("~")
            if len(parts) < 10:
                continue

            results.append({
                "name": parts[1],
                "code": parts[2],
                "price": float(parts[3]) if parts[3] else 0,
                "prev_close": float(parts[4]) if parts[4] else 0,
                "open": float(parts[5]) if parts[5] else 0,
                "volume": int(float(parts[6])) if parts[6] else 0,
                "high": float(parts[33]) if len(parts) > 33 and parts[33] else 0,
                "low": float(parts[34]) if len(parts) > 34 and parts[34] else 0,
                "pct_change": float(parts[32]) if len(parts) > 32 and parts[32] else 0,
                "turnover_rate": float(parts[38]) if len(parts) > 38 and parts[38] else 0,
                "pe_ttm": float(parts[39]) if len(parts) > 39 and parts[39] else 0,
            })

        spot_cache.set(cache_key, results, CACHE_TTL["spot"])
        return results
    except Exception as e:
        print(f"[realtime] Error: {e}")
        return []


# ── 市场概况（新浪源） ──

def get_market_overview() -> dict:
    """获取三大指数 + 涨跌统计"""
    cache_key = "market_overview"
    cached = spot_cache.get(cache_key)
    if cached:
        return cached

    try:
        s = _get_session()
        headers = {"Referer": "https://finance.sina.com.cn"}

        # 上证、深证、创业板指数
        resp = s.get("https://hq.sinajs.cn/list=sh000001,sz399001,sz399006",
                     headers=headers, timeout=10)
        resp.encoding = "gbk"

        indices = {}
        index_map = {"sh000001": "上证指数", "sz399001": "深证成指", "sz399006": "创业板指"}

        for line in resp.text.strip().split("\n"):
            if "=" not in line:
                continue
            code = line.split("hq_str_")[1].split("=")[0]
            data = line.split('"')[1].split(",")
            if len(data) < 4:
                continue
            # 指数格式: name, current, change, pct_change, volume, amount
            price = float(data[1])
            change = float(data[2])
            pct = float(data[3])
            # 验证合理性（涨跌幅应该在-20%到+20%之间）
            if abs(pct) > 20:
                # 可能是股票格式：name, open, prev_close, current, high, low...
                # current 在 [3]，prev_close 在 [2]
                if len(data) >= 5:
                    price = float(data[3])
                    prev_close = float(data[2])
                    change = price - prev_close
                    pct = (change / prev_close * 100) if prev_close else 0
            indices[index_map.get(code, code)] = {
                "name": data[0],
                "price": round(price, 2),
                "change": round(change, 2),
                "pct_change": round(pct, 2),
            }

        spot_cache.set(cache_key, indices, CACHE_TTL["spot"])
        return indices
    except Exception as e:
        print(f"[market_overview] Error: {e}")
        return {}


# ── 涨跌停板统计 ──

def get_limit_stats() -> dict:
    """获取全市场涨跌停家数统计"""
    cache_key = "limit_stats"
    cached = spot_cache.get(cache_key)
    if cached:
        return cached

    try:
        s = _get_session()
        headers = {"Referer": "https://finance.sina.com.cn"}
        # 获取全A股列表及涨跌幅
        resp = s.get("https://hq.sinajs.cn/list=sh000001,sz399001,sz399006",
                     headers=headers, timeout=5)
        # 新浪批量查询有限制，改用简单统计
        # 通过爬取涨跌停板列表页
        result = {
            "limit_up": 0,
            "limit_down": 0,
            "up_count": 0,
            "down_count": 0,
            "flat_count": 0,
            "note": "需要升级数据源",
        }
        spot_cache.set(cache_key, result, CACHE_TTL["spot"])
        return result
    except Exception:
        return {"limit_up": 0, "limit_down": 0, "up_count": 0, "down_count": 0}


# ── 板块资金流向 ──

def get_sector_moneyflow() -> list[dict]:
    """获取行业板块资金流向 Top10"""
    cache_key = "sector_moneyflow"
    cached = spot_cache.get(cache_key)
    if cached:
        return cached

    try:
        import akshare as ak
        df = ak.stock_sector_fund_flow_rank(indicator="今日", sector_type="行业资金流向")
        if df is None or df.empty:
            return []

        result = []
        for _, row in df.head(10).iterrows():
            result.append({
                "name": str(row.iloc[0]) if len(row) > 0 else "",
                "price_change": float(row.iloc[1]) if len(row) > 1 else 0,
                "net_inflow": float(row.iloc[2]) if len(row) > 2 else 0,
            })
        spot_cache.set(cache_key, result, CACHE_TTL["spot"])
        return result
    except Exception as e:
        print(f"[moneyflow] Error: {e}")
        return []


# ── 龙虎榜 ──

def get_lhb_top() -> list[dict]:
    """获取最近龙虎榜数据"""
    cache_key = "lhb"
    cached = spot_cache.get(cache_key)
    if cached:
        return cached

    try:
        import akshare as ak
        df = ak.stock_lhb_detail_em(date="")  # 最新
        if df is None or df.empty:
            return []

        result = []
        for _, row in df.head(20).iterrows():
            result.append({
                "code": str(row.get("代码", "")).zfill(6) if "代码" in row else "",
                "name": str(row.get("名称", row.get("股票名称", ""))),
                "close": float(row.get("收盘价", 0) or 0),
                "pct_change": float(row.get("涨跌幅", 0) or 0),
                "reason": str(row.get("上榜原因", row.get("解读", ""))),
                "turnover": float(row.get("成交额", 0) or 0),
            })
        spot_cache.set(cache_key, result, CACHE_TTL["spot"])
        return result
    except Exception as e:
        print(f"[lhb] Error: {e}")
        return []


# ── 个股分时数据 ──

def get_minute_data(code: str) -> list[dict]:
    """获取个股当日分时数据"""
    code = code.strip().zfill(6)
    cache_key = f"minute_{code}"
    cached = spot_cache.get(cache_key)
    if cached:
        return cached

    try:
        import akshare as ak
        df = ak.stock_zh_a_minute(symbol=code, period="1")
        if df is None or df.empty:
            return []

        result = []
        for _, row in df.iterrows():
            result.append({
                "time": str(row.iloc[0]),
                "price": float(row.iloc[1]),
                "volume": float(row.iloc[2]) if len(row) > 2 else 0,
                "avg_price": float(row.iloc[3]) if len(row) > 3 else 0,
            })
        spot_cache.set(cache_key, result, 30)  # 30秒缓存
        return result
    except Exception as e:
        print(f"[minute] Error for {code}: {e}")
        return []
