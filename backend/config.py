"""应用配置常量"""

from datetime import datetime

# 数据默认值（动态获取今天日期）
DEFAULT_START_DATE = "20230101"
DEFAULT_ADJUST = "qfq"  # 前复权


def get_default_end_date() -> str:
    """返回今天的日期字符串 YYYYMMDD"""
    return datetime.now().strftime("%Y%m%d")

# 回测默认值
DEFAULT_INITIAL_CAPITAL = 100_000
DEFAULT_COMMISSION = 0.0003  # 单边 0.03%
DEFAULT_SLIPPAGE = 0.001     # 滑点 0.1%

# 风险计算默认值
RISK_FREE_RATE = 0.025  # 无风险利率 2.5%
TRADING_DAYS_PER_YEAR = 252

# 建议引擎权重
SCORE_WEIGHTS = {
    "trend": 25,
    "momentum": 25,
    "valuation": 25,
    "risk": 25,
}

# 仓位限制
MIN_POSITION_PCT = 5
MAX_POSITION_PCT = 25

# 缓存 TTL（秒）
CACHE_TTL = {
    "price": 60,        # 1分钟（实时行情够用）
    "spot": 30,         # 30秒
    "valuation": 3600,  # 1小时
}

# 基准指数
BENCHMARK_INDEX = "sh000001"  # 上证指数
