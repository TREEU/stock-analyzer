import { useState } from 'react';
import ReactECharts from 'echarts-for-react';
import { useMemo } from 'react';

export default function BacktestPanel({ strategies = [], onRun, result, loading }) {
  const [strategy, setStrategy] = useState('ma_cross');
  const [params, setParams] = useState({ fast: 5, slow: 20 });

  const currentStrategy = strategies.find((s) => s.name === strategy);
  const defaultParams = currentStrategy?.params || {};

  const handleStrategyChange = (name) => {
    setStrategy(name);
    const s = strategies.find((s) => s.name === name);
    setParams(s?.params || {});
  };

  const handleParamChange = (key, val) => {
    setParams((p) => ({ ...p, [key]: parseFloat(val) || 0 }));
  };

  function today() {
    return new Date().toISOString().slice(0, 10).replace(/-/g, '');
  }

  const handleRun = () => {
    onRun({ strategy, params, start: '20230101', end: today(), initialCapital: 100000 });
  };

  // 权益曲线图表
  const equityOption = useMemo(() => {
    if (!result) return {};
    const eq = result.equity_curve || [];
    const bench = result.benchmark_equity || [];
    const dates = eq.map((d) => d.date);

    return {
      backgroundColor: 'transparent',
      grid: { left: 65, right: 15, top: 15, bottom: 25 },
      xAxis: {
        type: 'category', data: dates,
        axisLabel: { color: '#8b8fa3', fontSize: 10 },
        axisLine: { lineStyle: { color: '#2a2d3a' } },
      },
      yAxis: {
        type: 'value',
        axisLabel: { color: '#8b8fa3', fontSize: 10, formatter: (v) => `${(v / 10000).toFixed(0)}万` },
        splitLine: { lineStyle: { color: '#1a1d27' } },
      },
      series: [
        {
          name: '策略权益', type: 'line',
          data: eq.map((d) => d.equity),
          symbol: 'none', lineStyle: { color: '#448aff', width: 2 },
        },
        {
          name: '买入持有', type: 'line',
          data: bench.map((d) => d.equity),
          symbol: 'none', lineStyle: { color: '#8b8fa3', width: 1, type: 'dashed' },
        },
      ],
      tooltip: { trigger: 'axis', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 11 } },
      legend: { data: ['策略权益', '买入持有'], bottom: 0, textStyle: { color: '#8b8fa3', fontSize: 10 } },
    };
  }, [result]);

  const metrics = result?.metrics || {};
  const trades = result?.trades || [];

  return (
    <div className="panel">
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="backtest-controls">
          <div className="control-group">
            <label>策略</label>
            <select value={strategy} onChange={(e) => handleStrategyChange(e.target.value)}>
              {strategies.map((s) => (
                <option key={s.name} value={s.name}>{strategyLabel(s.name)}</option>
              ))}
            </select>
          </div>
          {Object.entries(params).map(([k, v]) => (
            <div className="control-group" key={k}>
              <label>{k}</label>
              <input
                type="number" step="1" min="1" max="250"
                value={v} onChange={(e) => handleParamChange(k, e.target.value)}
              />
            </div>
          ))}
          <div className="control-group" style={{ justifyContent: 'flex-end' }}>
            <button className="btn btn-primary" onClick={handleRun} disabled={loading}>
              {loading ? '回测中...' : '▶ 开始回测'}
            </button>
          </div>
        </div>
      </div>

      {result && (
        <>
          <div className="backtest-metrics">
            <div className="card metric-card">
              <div className={`metric-value ${metrics.total_return >= 0 ? 'green' : 'red'}`}>
                {metrics.total_return?.toFixed(1)}%
              </div>
              <div className="metric-label">总收益</div>
            </div>
            <div className="card metric-card">
              <div className={`metric-value ${metrics.excess_return >= 0 ? 'green' : 'red'}`}>
                {metrics.excess_return > 0 ? '+' : ''}{metrics.excess_return?.toFixed(1)}%
              </div>
              <div className="metric-label">超额收益 (vs 持有)</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value">{metrics.sharpe_ratio?.toFixed(2)}</div>
              <div className="metric-label">Sharpe</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value red">{metrics.max_drawdown?.toFixed(1)}%</div>
              <div className="metric-label">最大回撤</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value">{metrics.win_rate?.toFixed(0)}%</div>
              <div className="metric-label">胜率</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value">{metrics.profit_factor?.toFixed(2)}</div>
              <div className="metric-label">盈亏比</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value">{metrics.total_trades}</div>
              <div className="metric-label">交易次数</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value">{metrics.expectancy?.toFixed(2)}%</div>
              <div className="metric-label">期望值</div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 12 }}>
            <div className="card-title">权益曲线</div>
            <ReactECharts option={equityOption} style={{ height: 320 }} notMerge lazyUpdate />
          </div>

          {trades.length > 0 && (
            <div className="card">
              <div className="card-title">交易记录</div>
              <div style={{ maxHeight: 300, overflowY: 'auto' }}>
                <table className="trade-table">
                  <thead>
                    <tr>
                      <th>日期</th><th>操作</th><th>价格</th><th>股数</th>
                      <th>现金余额</th><th>权益</th><th>盈亏%</th>
                    </tr>
                  </thead>
                  <tbody>
                    {trades.map((t, i) => (
                      <tr key={i}>
                        <td>{t.date}</td>
                        <td className={t.action === 'buy' ? 'buy' : 'sell'}>
                          {t.action === 'buy' ? '买入' : '卖出'}
                          {t.note ? ` (${t.note})` : ''}
                        </td>
                        <td>¥{t.price?.toFixed(2)}</td>
                        <td>{t.shares?.toLocaleString()}</td>
                        <td>¥{t.cash_after?.toLocaleString()}</td>
                        <td>¥{t.equity?.toLocaleString()}</td>
                        <td className={t.pnl_pct >= 0 ? 'green' : 'red'}>
                          {t.pnl_pct != null ? `${t.pnl_pct > 0 ? '+' : ''}${t.pnl_pct}%` : '--'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}

      {!result && !loading && (
        <div className="empty-state" style={{ padding: '40px' }}>
          选择策略并点击「开始回测」查看历史表现
        </div>
      )}
    </div>
  );
}

function strategyLabel(name) {
  const map = {
    ma_cross: 'MA双均线交叉',
    macd_signal: 'MACD信号',
    rsi_mean_rev: 'RSI均值回归',
    boll_break: '布林带突破',
    boll_mean_rev: '布林带回归',
    triple_screen: '三重滤网',
    turtle_channel: '海龟通道',
  };
  return map[name] || name;
}
