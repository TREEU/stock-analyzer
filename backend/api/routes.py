"""API 路由定义"""

import math
from fastapi import APIRouter, HTTPException, Query
from backend.api.schemas import BacktestRequest
from backend.data.fetcher import (
    search_stocks,
    fetch_daily_price,
    fetch_stock_info,
)
from backend.config import DEFAULT_START_DATE, get_default_end_date

router = APIRouter(prefix="/api")


def _sanitize(obj):
    """递归清理 NaN/Infinity 值，替换为 None"""
    if isinstance(obj, dict):
        return {k: _sanitize(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_sanitize(v) for v in obj]
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
    return obj


# ── 股票搜索 ──

@router.get("/stock/search")
async def api_search_stocks(keyword: str = Query(..., min_length=1)):
    """按代码或名称搜索股票"""
    results = search_stocks(keyword)
    return {"keyword": keyword, "count": len(results), "results": results}


# ── 日线价格 ──

@router.get("/stock/{code}/price")
async def api_price(
    code: str,
    start: str = Query(default=DEFAULT_START_DATE),
    end: str = Query(default_factory=get_default_end_date),
    adjust: str = Query(default="qfq"),
):
    """获取单只股票日线数据"""
    info = fetch_stock_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {code}")

    df = fetch_daily_price(code, start, end, adjust)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"未获取到 {code} 的价格数据")

    # 只返回必要字段，NaN 替换为 None
    cols = ["date", "open", "close", "high", "low", "volume",
            "amount", "amplitude", "pct_change", "turnover_rate"]
    available_cols = [c for c in cols if c in df.columns]
    data = df[available_cols].where(df[available_cols].notna(), None).to_dict(orient="records")

    return {
        "code": code,
        "name": info.get("name", ""),
        "count": len(data),
        "data": data,
    }


# ── 股票基本信息 ──

@router.get("/stock/{code}/info")
async def api_stock_info(code: str):
    """获取股票基本信息"""
    info = fetch_stock_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {code}")
    return info


# ── 技术指标（延迟导入，避免循环依赖） ──

@router.get("/stock/{code}/indicators")
async def api_indicators(
    code: str,
    start: str = Query(default=DEFAULT_START_DATE),
    end: str = Query(default_factory=get_default_end_date),
):
    """计算技术指标"""
    info = fetch_stock_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {code}")

    df = fetch_daily_price(code, start, end)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"未获取到价格数据")

    from backend.analysis.technical import compute_indicators
    result = compute_indicators(df)
    result["code"] = code
    result["name"] = info.get("name", "")
    return _sanitize(result)


# ── 估值分析 ──

@router.get("/stock/{code}/valuation")
async def api_valuation(code: str):
    """估值分析"""
    info = fetch_stock_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {code}")

    from backend.analysis.valuation import assess_valuation
    result = assess_valuation(code, info)
    result["code"] = code
    result["name"] = info.get("name", "")
    return result


# ── 风险分析 ──

@router.get("/stock/{code}/risk")
async def api_risk(
    code: str,
    start: str = Query(default=DEFAULT_START_DATE),
    end: str = Query(default_factory=get_default_end_date),
):
    """风险指标分析"""
    info = fetch_stock_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {code}")

    df = fetch_daily_price(code, start, end)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"未获取到价格数据")

    from backend.analysis.risk import compute_risk_metrics
    result = compute_risk_metrics(df, code)
    result["code"] = code
    result["name"] = info.get("name", "")
    return result


# ── 操作建议 ──

@router.get("/stock/{code}/recommendation")
async def api_recommendation(
    code: str,
    start: str = Query(default=DEFAULT_START_DATE),
    end: str = Query(default_factory=get_default_end_date),
):
    """生成操作建议"""
    info = fetch_stock_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {code}")

    df = fetch_daily_price(code, start, end)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"未获取到价格数据")

    from backend.analysis.technical import compute_indicators
    from backend.analysis.valuation import assess_valuation
    from backend.analysis.risk import compute_risk_metrics
    from backend.analysis.recommendation import generate_recommendation

    indicators = compute_indicators(df)
    valuation = assess_valuation(code, info)
    risk = compute_risk_metrics(df, code)

    result = generate_recommendation(indicators, valuation, risk)
    result["code"] = code
    result["name"] = info.get("name", "")
    return result


# ── 综合分析（一次返回全部） ──

@router.get("/stock/{code}/full-analysis")
async def api_full_analysis(
    code: str,
    start: str = Query(default=DEFAULT_START_DATE),
    end: str = Query(default_factory=get_default_end_date),
):
    """一次请求获取所有分析数据"""
    info = fetch_stock_info(code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {code}")

    df = fetch_daily_price(code, start, end)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"未获取到 {code} 的价格数据")

    from backend.analysis.technical import compute_indicators
    from backend.analysis.valuation import assess_valuation
    from backend.analysis.risk import compute_risk_metrics
    from backend.analysis.recommendation import generate_recommendation

    # 价格数据简化输出
    cols = ["date", "open", "close", "high", "low", "volume",
            "amount", "amplitude", "pct_change", "turnover_rate"]
    available_cols = [c for c in cols if c in df.columns]
    price_data = df[available_cols].where(df[available_cols].notna(), None).to_dict(orient="records")

    # 各模块分析
    indicators = compute_indicators(df)
    valuation = assess_valuation(code, info)
    risk = compute_risk_metrics(df, code)
    recommendation = generate_recommendation(indicators, valuation, risk)

    return _sanitize({
        "code": code,
        "name": info.get("name", ""),
        "stock_info": info,
        "price_data": price_data,
        "indicators": {**indicators, "code": code, "name": info.get("name", "")},
        "valuation": {**valuation, "code": code, "name": info.get("name", "")},
        "risk": {**risk, "code": code, "name": info.get("name", "")},
        "recommendation": {**recommendation, "code": code, "name": info.get("name", "")},
    })


# ── 策略回测 ──

@router.post("/backtest")
async def api_backtest(req: BacktestRequest):
    """执行策略回测"""
    info = fetch_stock_info(req.code)
    if not info:
        raise HTTPException(status_code=404, detail=f"未找到股票: {req.code}")

    df = fetch_daily_price(req.code, req.start, req.end)
    if df is None or df.empty:
        raise HTTPException(status_code=404, detail=f"未获取到价格数据")

    from backend.backtest.engine import BacktestEngine
    from backend.backtest.strategies import get_strategy

    strategy_cls = get_strategy(req.strategy)
    if strategy_cls is None:
        raise HTTPException(status_code=400,
                            detail=f"未知策略: {req.strategy}。可用策略: {get_available_strategies()}")

    strategy_params = req.params if req.params else {}
    strategy = strategy_cls(**strategy_params)

    engine = BacktestEngine(
        df=df,
        initial_capital=req.initial_capital,
    )

    result = engine.run(strategy)
    result["code"] = req.code
    result["strategy"] = req.strategy
    result["params"] = strategy_params
    return _sanitize(result)


@router.get("/backtest/strategies")
async def api_list_strategies():
    """列出所有可用策略"""
    from backend.backtest.strategies import STRATEGY_REGISTRY
    return {
        "strategies": [
            {"name": name, "params": cls.default_params()}
            for name, cls in STRATEGY_REGISTRY.items()
        ]
    }


def get_available_strategies() -> list[str]:
    from backend.backtest.strategies import STRATEGY_REGISTRY
    return list(STRATEGY_REGISTRY.keys())


# ── 实时行情（新增） ──

@router.get("/market/realtime")
async def api_realtime(codes: str = Query(..., description="股票代码逗号分隔，如 000001,600519")):
    """获取多只股票实时行情"""
    code_list = [c.strip() for c in codes.split(",") if c.strip()]
    from backend.data.market import get_realtime_quotes
    results = get_realtime_quotes(code_list)
    return {"codes": codes, "data": results}


@router.get("/market/overview")
async def api_market_overview():
    """三大指数实时行情"""
    from backend.data.market import get_market_overview
    return get_market_overview()


@router.get("/market/minutekline/{code}")
async def api_minute_kline(code: str):
    """个股分时数据"""
    from backend.data.market import get_minute_data
    data = get_minute_data(code)
    return {"code": code, "data": data}


@router.get("/market/sector-flow")
async def api_sector_flow():
    """行业板块资金流向"""
    from backend.data.market import get_sector_moneyflow
    data = get_sector_moneyflow()
    return {"data": data}


@router.get("/market/lhb")
async def api_lhb():
    """龙虎榜"""
    from backend.data.market import get_lhb_top
    data = get_lhb_top()
    return {"data": data}


@router.get("/market/search-realtime")
async def api_search_realtime(keyword: str = Query(..., min_length=1)):
    """搜索股票+实时行情（一次请求拿结果）"""
    results = search_stocks(keyword)
    if not results:
        return {"results": []}

    codes = [r["code"] for r in results[:10]]
    from backend.data.market import get_realtime_quotes
    quotes = get_realtime_quotes(codes)
    quote_map = {q["code"]: q for q in quotes}

    enriched = []
    for r in results[:10]:
        q = quote_map.get(r["code"], {})
        enriched.append({
            **r,
            "price": q.get("price", 0),
            "pct_change": q.get("pct_change", 0),
            "pe_ttm": q.get("pe_ttm", 0),
            "volume": q.get("volume", 0),
            "turnover_rate": q.get("turnover_rate", 0),
        })

    return {"results": enriched}


# ── 持仓管理 ──

@router.get("/portfolio")
async def api_get_portfolio():
    """获取全部持仓"""
    from backend.data.portfolio import get_holdings
    return get_holdings()


@router.post("/portfolio/add")
async def api_add_holding(data: dict):
    """添加持仓 (JSON body: {code, name, cost_price, quantity, notes})"""
    from backend.data.portfolio import add_holding
    holding = add_holding(
        code=data.get("code", ""),
        name=data.get("name", ""),
        cost_price=data.get("cost_price", 0),
        quantity=data.get("quantity", 0),
        notes=data.get("notes", ""),
    )
    return {"ok": True, "holding": holding}


@router.put("/portfolio/{holding_id}")
async def api_update_holding(
    holding_id: str,
    cost_price: float = Query(default=None),
    quantity: int = Query(default=None),
    notes: str = Query(default=None),
):
    """更新持仓"""
    from backend.data.portfolio import update_holding
    kwargs = {}
    if cost_price is not None:
        kwargs["cost_price"] = cost_price
    if quantity is not None:
        kwargs["quantity"] = quantity
    if notes is not None:
        kwargs["notes"] = notes
    result = update_holding(holding_id, **kwargs)
    if result is None:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"ok": True, "holding": result}


@router.delete("/portfolio/{holding_id}")
async def api_delete_holding(holding_id: str):
    """删除持仓"""
    from backend.data.portfolio import delete_holding
    ok = delete_holding(holding_id)
    if not ok:
        raise HTTPException(status_code=404, detail="持仓不存在")
    return {"ok": True}


@router.delete("/portfolio")
async def api_clear_portfolio():
    """清空全部持仓"""
    from backend.data.portfolio import clear_holdings
    count = clear_holdings()
    return {"ok": True, "cleared": count}


# ── 买卖时机分析 ──

@router.get("/portfolio/analyze")
async def api_portfolio_analyze():
    """分析所有持仓的买卖时机"""
    from backend.data.portfolio import get_holdings
    from backend.analysis.timing import analyze_timing

    holdings = get_holdings()["holdings"]
    results = []
    for h in holdings:
        timing = analyze_timing(h["code"], h["cost_price"])
        timing["holding_id"] = h["id"]
        timing["cost_price"] = h["cost_price"]
        timing["quantity"] = h["quantity"]
        timing["added_at"] = h.get("added_at", "")
        # 名字解析
        # 名字解析：优先实时查，兜底用存储的
        stored_name = h.get("name", "")
        if not stored_name or stored_name == h["code"] or stored_name.isdigit():
            info = fetch_stock_info(h["code"])
            if info and info.get("name") and info["name"] != h["code"]:
                stored_name = info["name"]
        timing["name"] = stored_name or h["code"]
        results.append(timing)

    # 按信号优先级排序：buy > hold > sell
    signal_order = {"buy": 0, "hold": 1, "sell": 2}
    results.sort(key=lambda x: signal_order.get(x.get("signal", "hold"), 1))

    return {"holdings": results, "updated_at": get_holdings()["updated_at"]}


@router.get("/portfolio/analyze/{code}")
async def api_single_timing(code: str, cost_price: float = Query(default=0)):
    """单只股票买卖时机分析"""
    from backend.analysis.timing import analyze_timing
    return analyze_timing(code, cost_price)


# ── 综合回测验证 ──

@router.get("/validate/{code}")
async def api_comprehensive_validate(
    code: str,
    start: str = Query(default="20210101"),
    end: str = Query(default_factory=get_default_end_date),
):
    """全面验证：多策略对比 + 牛熊分段 + 滚动窗口 + 参数敏感性"""
    from backend.backtest.validator import comprehensive_validate
    return comprehensive_validate(code, start, end)
