"""Pydantic 请求/响应模型"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


def _today() -> str:
    return datetime.now().strftime("%Y%m%d")


# ── 请求模型 ──

class BacktestRequest(BaseModel):
    code: str = Field(..., description="股票代码，如 000001")
    strategy: str = Field(default="ma_cross", description="策略名称")
    params: dict = Field(default_factory=dict, description="策略参数")
    start: str = Field(default="20230101", description="回测起始日期 YYYYMMDD")
    end: str = Field(default_factory=_today, description="回测结束日期 YYYYMMDD")
    initial_capital: float = Field(default=100000, description="初始资金")


# ── 响应模型 ──

class StockInfo(BaseModel):
    code: str
    name: str
    latest_price: float = 0
    pct_change: float = 0
    pe_ttm: float = 0
    pb: float = 0
    market_cap: float = 0
    turnover_rate: float = 0


class PriceDataPoint(BaseModel):
    date: str
    open: float
    close: float
    high: float
    low: float
    volume: float
    amount: Optional[float] = None
    amplitude: Optional[float] = None
    pct_change: Optional[float] = None
    turnover_rate: Optional[float] = None


class IndicatorsResponse(BaseModel):
    code: str
    name: str
    data: list[dict]  # 每行包含 date + 所有指标值
    latest_signals: dict  # 最新交易日的信号摘要


class ValuationResponse(BaseModel):
    code: str
    name: str
    pe_ttm: float
    pb: float
    pe_percentile: Optional[float] = None
    pb_percentile: Optional[float] = None
    index_pe: Optional[float] = None
    index_pb: Optional[float] = None
    assessment: str  # undervalued / fair / overvalued


class RiskResponse(BaseModel):
    code: str
    name: str
    var_95: float
    var_99: float
    cvar_95: float
    sharpe_ratio: float
    max_drawdown: float
    max_drawdown_duration: int
    annual_volatility: float
    annual_return: float
    calmar_ratio: float
    beta: Optional[float] = None
    win_rate: float
    total_days: int


class RecommendationResponse(BaseModel):
    code: str
    name: str
    total_score: float
    signal: str  # buy / hold / sell
    confidence: str  # high / medium / low
    position_pct: float
    reasons: list[str]
    risks: list[str]
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None
    latest_price: float = 0
    trend_score: float = 0
    momentum_score: float = 0
    valuation_score: float = 0
    risk_score: float = 0


class BacktestTrade(BaseModel):
    date: str
    action: str  # buy / sell
    price: float
    shares: int
    cash_after: float
    equity: float
    pnl_pct: Optional[float] = None


class BacktestMetrics(BaseModel):
    total_return: float
    annual_return: float
    benchmark_return: float
    excess_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    total_trades: int
    max_consecutive_losses: int
    expectancy: float


class BacktestResponse(BaseModel):
    code: str
    strategy: str
    params: dict
    trades: list[dict]
    metrics: dict
    equity_curve: list[dict]
    benchmark_equity: list[dict]


class FullAnalysisResponse(BaseModel):
    code: str
    name: str
    stock_info: StockInfo
    price_data: list[dict]
    indicators: IndicatorsResponse
    valuation: ValuationResponse
    risk: RiskResponse
    recommendation: RecommendationResponse
