# A股量化分析平台

个人A股持仓量化分析工具，支持技术指标、估值分析、风险度量、策略回测和操作建议。

## 快速开始

### 1. 安装依赖

```bash
# Python 后端
pip install fastapi uvicorn pandas numpy akshare httpx pydantic

# 前端
cd frontend && npm install && cd ..
```

### 2. 启动

```bash
# 一键启动
bash start.sh

# 或分别启动：
# 后端
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 前端（新终端）
cd frontend && npm run dev
```

### 3. 使用

1. 打开 http://localhost:5173
2. 搜索框输入股票代码或名称（如 `000001` 或 `平安银行`）
3. 查看 K线图 + 技术指标
4. 切换到「策略回测」Tab，选策略跑回测
5. 查看「操作建议」Tab 获取得分和操作信号

## 功能模块

| 模块 | 功能 |
|------|------|
| **技术指标** | MA(5/10/20/60/120/250)、MACD、RSI(14)、KDJ、Bollinger Bands、ATR、成交量均线 |
| **估值分析** | PE/PB 当前值 + 历史分位 + 沪深300参考 + 综合估值评级 |
| **风险评估** | VaR(95%/99%)、CVaR、Sharpe、Max Drawdown、年化波动、Calmar、Beta、日胜率 |
| **策略回测** | 7种策略（MA交叉/MACD/RSI回归/布林突破/布林回归/三重滤网/海龟通道） |
| **操作建议** | 四维度加权评分 → 买/持/卖信号 + 建议仓位 + 止盈止损价 |

## 技术栈

- **后端**: FastAPI + akshare (腾讯数据源) + pandas + numpy
- **前端**: React 18 + Vite + ECharts
- **数据源**: 腾讯财经 API (稳定可靠)
