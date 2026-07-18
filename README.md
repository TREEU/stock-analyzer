# A股量化分析平台

个人A股持仓量化分析工具，支持**实时行情**、技术指标、估值分析、风险度量、策略回测和操作建议。

> 📱 手机访问：确保电脑和手机在同一 WiFi，浏览器打开 `http://192.168.2.19:5173`

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
# 一键启动（电脑+手机均可访问）
bash start.sh

# 或分别启动：
# 后端
python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000

# 前端（新终端，--host 允许局域网访问）
cd frontend && npm run dev -- --host 0.0.0.0
```

### 3. 使用

**电脑端：**
1. 打开 http://localhost:5173
2. 📡 实时行情 Tab 看三大指数+板块资金流向
3. 搜索框输入股票代码或名称（如 `000001` 或 `平安银行`）
4. 切换到「策略回测」Tab，选策略跑回测
5. 查看「操作建议」Tab 获取得分和操作信号

**手机端：**
- 确保手机和电脑连同一个 WiFi
- 浏览器打开 `http://192.168.2.19:5173`

## 功能模块

| 模块 | 功能 |
|------|------|
| 📡 **实时行情** | 三大指数、个股实时价+PE/PB、行业资金流向、每10秒自动刷新 |
| **技术指标** | MA(5/10/20/60/120/250)、MACD、RSI(14)、KDJ、Bollinger Bands、ATR |
| **估值分析** | PE/PB 当前值 + 分位 + 沪深300参考 + 综合评级 |
| **风险评估** | VaR(95%/99%)、CVaR、Sharpe、Max Drawdown、Beta |
| **策略回测** | 7种策略（MA交叉/MACD/RSI回归/布林突破/布林回归/三重滤网/海龟通道） |
| **操作建议** | 四维度加权评分 → 买/持/卖信号 + 仓位 + 止盈止损 |

## 技术栈

- **后端**: FastAPI + 腾讯/新浪双数据源 + pandas + numpy
- **前端**: React 18 + Vite + ECharts
- **MCP**: ashare-mcp（30个金融数据工具）
- **仓库**: [github.com/TREEU/stock-analyzer](https://github.com/TREEU/stock-analyzer)
