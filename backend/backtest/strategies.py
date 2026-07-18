"""回测策略实现

所有策略继承 BaseStrategy，实现 generate_signals 方法。
返回值为 pd.Series: 1=buy/持仓, 0=空仓/sell, -1=sell
"""
from __future__ import annotations

import pandas as pd
import numpy as np


class BaseStrategy:
    name: str = "base"

    def __init__(self, **params):
        self.params = params

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        raise NotImplementedError

    @classmethod
    def default_params(cls) -> dict:
        return {}


class MACrossoverStrategy(BaseStrategy):
    """MA双均线交叉策略 — 趋势跟踪"""
    name = "ma_cross"

    def __init__(self, fast: int = 5, slow: int = 20, **kwargs):
        super().__init__(fast=fast, slow=slow, **kwargs)
        self.fast = fast
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        ma_fast = close.rolling(self.fast).mean()
        ma_slow = close.rolling(self.slow).mean()

        signals = pd.Series(0, index=df.index)
        # 金叉买入
        signals[(ma_fast > ma_slow) & (ma_fast.shift(1) <= ma_slow.shift(1))] = 1
        # 死叉卖出
        signals[(ma_fast < ma_slow) & (ma_fast.shift(1) >= ma_slow.shift(1))] = -1

        return signals

    @classmethod
    def default_params(cls) -> dict:
        return {"fast": 5, "slow": 20}


class MACDSignalStrategy(BaseStrategy):
    """MACD 信号策略 — 动量"""
    name = "macd_signal"

    def __init__(self, fast: int = 12, slow: int = 26, signal: int = 9, **kwargs):
        super().__init__(fast=fast, slow=slow, signal=signal, **kwargs)
        self.fast = fast
        self.slow = slow
        self.signal = signal

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)

        ema_fast = close.ewm(span=self.fast, adjust=False).mean()
        ema_slow = close.ewm(span=self.slow, adjust=False).mean()
        dif = ema_fast - ema_slow
        dea = dif.ewm(span=self.signal, adjust=False).mean()

        signals = pd.Series(0, index=df.index)
        signals[(dif > dea) & (dif.shift(1) <= dea.shift(1))] = 1
        signals[(dif < dea) & (dif.shift(1) >= dea.shift(1))] = -1

        return signals

    @classmethod
    def default_params(cls) -> dict:
        return {"fast": 12, "slow": 26, "signal": 9}


class RSIMeanRevStrategy(BaseStrategy):
    """RSI 均值回归策略"""
    name = "rsi_mean_rev"

    def __init__(self, period: int = 14, oversold: int = 30, overbought: int = 70, **kwargs):
        super().__init__(period=period, oversold=oversold, overbought=overbought, **kwargs)
        self.period = period
        self.oversold = oversold
        self.overbought = overbought

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        delta = close.diff()
        gain = delta.clip(lower=0)
        loss = (-delta).clip(lower=0)
        avg_gain = gain.rolling(self.period).mean()
        avg_loss = loss.rolling(self.period).mean()

        # 使用 EMA 平滑
        avg_gain = gain.ewm(span=self.period, adjust=False).mean()
        avg_loss = loss.ewm(span=self.period, adjust=False).mean()

        rs = avg_gain / avg_loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(0, index=df.index)
        # 超卖区回升买入
        signals[(rsi > self.oversold) & (rsi.shift(1) <= self.oversold)] = 1
        # 超买区回落卖出
        signals[(rsi < self.overbought) & (rsi.shift(1) >= self.overbought)] = -1

        return signals

    @classmethod
    def default_params(cls) -> dict:
        return {"period": 14, "oversold": 30, "overbought": 70}


class BollBreakStrategy(BaseStrategy):
    """布林带突破策略 — 波动突破"""
    name = "boll_break"

    def __init__(self, period: int = 20, std: float = 2.0, **kwargs):
        super().__init__(period=period, std=std, **kwargs)
        self.period = period
        self.std = std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        mid = close.rolling(self.period).mean()
        std_dev = close.rolling(self.period).std()
        upper = mid + self.std * std_dev
        lower = mid - self.std * std_dev

        signals = pd.Series(0, index=df.index)
        # 收盘突破上轨买入
        signals[(close > upper) & (close.shift(1) <= upper.shift(1))] = 1
        # 收盘跌破中轨卖出
        signals[(close < mid) & (close.shift(1) >= mid.shift(1))] = -1

        return signals

    @classmethod
    def default_params(cls) -> dict:
        return {"period": 20, "std": 2.0}


class BollMeanRevStrategy(BaseStrategy):
    """布林带均值回归策略"""
    name = "boll_mean_rev"

    def __init__(self, period: int = 20, std: float = 2.0, **kwargs):
        super().__init__(period=period, std=std, **kwargs)
        self.period = period
        self.std = std

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)
        mid = close.rolling(self.period).mean()
        std_dev = close.rolling(self.period).std()
        lower = mid - self.std * std_dev

        signals = pd.Series(0, index=df.index)
        # 收盘跌破下轨买入（均值回归）
        signals[(close < lower) & (close.shift(1) >= lower.shift(1))] = 1
        # 回升到中轨卖出
        signals[(close > mid) & (close.shift(1) <= mid.shift(1))] = -1

        return signals

    @classmethod
    def default_params(cls) -> dict:
        return {"period": 20, "std": 2.0}


class TripleScreenStrategy(BaseStrategy):
    """三重滤网策略 — 多时间框架确认"""
    name = "triple_screen"

    def __init__(self, fast: int = 5, mid: int = 20, slow: int = 60, **kwargs):
        super().__init__(fast=fast, mid=mid, slow=slow, **kwargs)
        self.fast = fast
        self.mid = mid
        self.slow = slow

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)

        if len(close) < self.slow:
            return pd.Series(0, index=df.index)

        ma_fast = close.rolling(self.fast).mean()
        ma_mid = close.rolling(self.mid).mean()
        ma_slow = close.rolling(self.slow).mean()

        # 计算 MACD
        ema12 = close.ewm(span=12, adjust=False).mean()
        ema26 = close.ewm(span=26, adjust=False).mean()
        dif = ema12 - ema26
        dea = dif.ewm(span=9, adjust=False).mean()

        # 计算 RSI
        delta = close.diff()
        gain = delta.clip(lower=0).ewm(span=14, adjust=False).mean()
        loss = (-delta).clip(lower=0).ewm(span=14, adjust=False).mean()
        rs = gain / loss.replace(0, np.nan)
        rsi = 100 - (100 / (1 + rs))

        signals = pd.Series(0, index=df.index)

        # 三重确认买入：
        # 1. 潮汐：MA快 > MA中 > MA慢（上升趋势）
        # 2. 波浪：MACD 金叉或 DIF > DEA
        # 3. 浪花：RSI 不超买（<70）
        tide = (ma_fast > ma_mid) & (ma_mid > ma_slow)
        wave = (dif > dea) & (dif.shift(1) <= dea.shift(1))  # 金叉
        ripple = rsi < 70

        buy_signal = tide & wave & ripple
        signals[buy_signal] = 1

        # 卖出条件：趋势破坏
        sell_signal = (ma_fast < ma_mid) | (dif < dea)
        # 只在持仓后可能卖出
        signals[sell_signal & (signals.shift(1) != -1)] = -1

        return signals

    @classmethod
    def default_params(cls) -> dict:
        return {"fast": 5, "mid": 20, "slow": 60}


class TurtleChannelStrategy(BaseStrategy):
    """海龟通道策略 — 趋势突破"""
    name = "turtle_channel"

    def __init__(self, entry: int = 20, exit_period: int = 10, **kwargs):
        super().__init__(entry=entry, exit_period=exit_period, **kwargs)
        self.entry = entry
        self.exit_period = exit_period

    def generate_signals(self, df: pd.DataFrame) -> pd.Series:
        close = df["close"].astype(float)

        entry_high = close.rolling(self.entry).max()
        exit_low = close.rolling(self.exit_period).min()

        signals = pd.Series(0, index=df.index)

        # 突破N日高点买入
        signals[(close > entry_high.shift(1))] = 1
        # 跌破M日低点卖出
        signals[(close < exit_low.shift(1))] = -1

        return signals

    @classmethod
    def default_params(cls) -> dict:
        return {"entry": 20, "exit_period": 10}


# ── 策略注册表 ──

STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "ma_cross": MACrossoverStrategy,
    "macd_signal": MACDSignalStrategy,
    "rsi_mean_rev": RSIMeanRevStrategy,
    "boll_break": BollBreakStrategy,
    "boll_mean_rev": BollMeanRevStrategy,
    "triple_screen": TripleScreenStrategy,
    "turtle_channel": TurtleChannelStrategy,
}


def get_strategy(name: str) -> type[BaseStrategy] | None:
    """根据名称获取策略类"""
    return STRATEGY_REGISTRY.get(name)
