import ReactECharts from 'echarts-for-react';
import { useMemo } from 'react';

export default function RiskPanel({ risk, priceData = [] }) {
  const metrics = risk || {};

  // 计算回撤曲线
  const drawdownData = useMemo(() => {
    if (!priceData.length) return [];
    const closes = priceData.map((d) => d.close);
    let peak = closes[0];
    return priceData.map((d, i) => {
      if (closes[i] > peak) peak = closes[i];
      const dd = (closes[i] - peak) / peak * 100;
      return { date: d.date, dd };
    });
  }, [priceData]);

  const ddOption = useMemo(() => ({
    backgroundColor: 'transparent',
    grid: { left: 55, right: 15, top: 15, bottom: 25 },
    xAxis: {
      type: 'category',
      data: drawdownData.map((d) => d.date),
      axisLabel: { color: '#8b8fa3', fontSize: 10 },
      axisLine: { lineStyle: { color: '#2a2d3a' } },
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#8b8fa3', fontSize: 10, formatter: '{value}%' },
      splitLine: { lineStyle: { color: '#1a1d27' } },
    },
    series: [{
      name: '回撤', type: 'line', data: drawdownData.map((d) => d.dd),
      symbol: 'none',
      lineStyle: { color: '#ff3d4f', width: 1 },
      areaStyle: { color: 'rgba(255,61,79,0.1)' },
    }],
    tooltip: { trigger: 'axis', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 11 } },
  }), [drawdownData]);

  const metricItems = [
    { label: '年化收益', value: metrics.annual_return != null ? `${metrics.annual_return.toFixed(1)}%` : '--', cls: metrics.annual_return > 0 ? 'green' : 'red' },
    { label: '年化波动', value: metrics.annual_volatility != null ? `${metrics.annual_volatility.toFixed(1)}%` : '--' },
    { label: 'Sharpe', value: metrics.sharpe_ratio != null ? metrics.sharpe_ratio.toFixed(2) : '--', cls: metrics.sharpe_ratio > 1 ? 'green' : '' },
    { label: 'Calmar', value: metrics.calmar_ratio != null ? metrics.calmar_ratio.toFixed(2) : '--' },
    { label: '最大回撤', value: metrics.max_drawdown != null ? `${metrics.max_drawdown.toFixed(1)}%` : '--', cls: Math.abs(metrics.max_drawdown) < 15 ? 'green' : Math.abs(metrics.max_drawdown) > 30 ? 'red' : '' },
    { label: '回撤天数', value: metrics.max_drawdown_duration || '--' },
    { label: 'VaR(95%)', value: metrics.var_95 != null ? `${metrics.var_95.toFixed(2)}%` : '--' },
    { label: 'CVaR(95%)', value: metrics.cvar_95 != null ? `${metrics.cvar_95.toFixed(2)}%` : '--' },
    { label: 'Beta', value: metrics.beta != null ? metrics.beta.toFixed(2) : '--' },
    { label: '日胜率', value: metrics.win_rate != null ? `${metrics.win_rate.toFixed(1)}%` : '--' },
    { label: '交易日', value: metrics.total_days || '--' },
    { label: 'VaR(99%)', value: metrics.var_99 != null ? `${metrics.var_99.toFixed(2)}%` : '--' },
  ];

  return (
    <div className="panel">
      <div className="backtest-metrics">
        {metricItems.map((m) => (
          <div className="card metric-card" key={m.label}>
            <div className={`metric-value ${m.cls || ''}`}>{m.value}</div>
            <div className="metric-label">{m.label}</div>
          </div>
        ))}
      </div>
      <div className="card">
        <div className="card-title">回撤曲线</div>
        <ReactECharts option={ddOption} style={{ height: 260 }} notMerge lazyUpdate />
      </div>
    </div>
  );
}
