export default function KeyMetricsBar({ stockInfo, indicators, risk }) {
  const latestPrice = stockInfo?.latest_price || 0;
  const pctChange = stockInfo?.pct_change || 0;
  const latestRsi = indicators?.latest_signals?.latest_rsi;
  const pe = stockInfo?.pe_ttm;
  const sharpe = risk?.sharpe_ratio;
  const maxDd = risk?.max_drawdown;

  const rsi = indicators?.data?.length
    ? indicators.data[indicators.data.length - 1]?.rsi
    : null;

  const metrics = [
    { label: '最新价', value: latestPrice ? `¥${latestPrice.toFixed(2)}` : '--', cls: pctChange >= 0 ? 'green' : 'red' },
    { label: '涨跌幅', value: pctChange ? `${pctChange > 0 ? '+' : ''}${pctChange.toFixed(2)}%` : '--', cls: pctChange >= 0 ? 'green' : 'red' },
    { label: 'RSI(14)', value: rsi != null ? rsi.toFixed(1) : '--', cls: rsi > 70 ? 'red' : rsi < 30 ? 'green' : '' },
    { label: 'PE(TTM)', value: pe > 0 ? pe.toFixed(1) : '--', cls: '' },
    { label: 'Sharpe', value: sharpe != null ? sharpe.toFixed(2) : '--', cls: sharpe > 1 ? 'green' : sharpe < 0 ? 'red' : '' },
    { label: '最大回撤', value: maxDd != null ? `${maxDd.toFixed(1)}%` : '--', cls: Math.abs(maxDd) < 15 ? 'green' : Math.abs(maxDd) > 30 ? 'red' : '' },
  ];

  return (
    <div className="metrics-row">
      {metrics.map((m) => (
        <div className="card metric-card" key={m.label}>
          <div className={`metric-value ${m.cls}`}>{m.value}</div>
          <div className="metric-label">{m.label}</div>
        </div>
      ))}
    </div>
  );
}
