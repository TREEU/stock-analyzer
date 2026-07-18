import { useState, useEffect, useRef, useMemo } from 'react';
import ReactECharts from 'echarts-for-react';

const API = `http://${window.location.hostname}:8000/api`;

export default function BacktestPanel({ strategies = [], onRun, result, loading, code }) {
  const [strategy, setStrategy] = useState('ma_cross');
  const [params, setParams] = useState({ fast: 5, slow: 20 });
  const [mode, setMode] = useState('simple'); // simple | comprehensive
  const [validation, setValidation] = useState(null);
  const [valLoading, setValLoading] = useState(false);

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

  function today() { return new Date().toISOString().slice(0, 10).replace(/-/g, ''); }
  function yearsAgo(n) { const d = new Date(); d.setFullYear(d.getFullYear()-n); return d.toISOString().slice(0,10).replace(/-/g,''); }
  function monthsAgo(n) { const d = new Date(); d.setMonth(d.getMonth()-n); return d.toISOString().slice(0,10).replace(/-/g,''); }

  // 时间范围（综合验证用）
  const [valStart, setValStart] = useState(monthsAgo(6));
  const [valEnd, setValEnd] = useState(today());

  const handleRun = () => {
    setMode('simple');
    onRun({ strategy, params, start: '20230101', end: today(), initialCapital: 100000 });
  };

  // 综合验证
  const handleValidate = async () => {
    if (!code) return;
    setMode('comprehensive');
    setValLoading(true);
    try {
      const r = await fetch(`${API}/validate/${code}?start=${valStart}&end=${valEnd}`);
      const d = await r.json();
      setValidation(d);
    } catch (e) {
      console.error(e);
    }
    setValLoading(false);
  };
  const handleValidateRef = useRef(handleValidate);
  handleValidateRef.current = handleValidate;

  // ── 单策略图表（保持原逻辑） ──
  const equityOption = useMemo(() => {
    if (!result) return {};
    const eq = result.equity_curve || [];
    const bench = result.benchmark_equity || [];
    const dates = eq.map((d) => d.date);

    return {
      backgroundColor: 'transparent',
      grid: { left: 65, right: 15, top: 15, bottom: 25 },
      xAxis: { type: 'category', data: dates, axisLabel: { color: '#8b8fa3', fontSize: 10 }, axisLine: { lineStyle: { color: '#2a2d3a' } } },
      yAxis: { type: 'value', axisLabel: { color: '#8b8fa3', fontSize: 10, formatter: (v) => `${(v / 10000).toFixed(0)}万` }, splitLine: { lineStyle: { color: '#1a1d27' } } },
      series: [
        { name: '策略权益', type: 'line', data: eq.map((d) => d.equity), symbol: 'none', lineStyle: { color: '#448aff', width: 2 } },
        { name: '买入持有', type: 'line', data: bench.map((d) => d.equity), symbol: 'none', lineStyle: { color: '#8b8fa3', width: 1, type: 'dashed' } },
      ],
      tooltip: { trigger: 'axis', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 11 } },
      legend: { data: ['策略权益', '买入持有'], bottom: 0, textStyle: { color: '#8b8fa3', fontSize: 10 } },
    };
  }, [result]);

  const metrics = result?.metrics || {};
  const trades = result?.trades || [];

  return (
    <div className="panel">
      {/* 模式切换 + 策略选择 */}
      <div className="card" style={{ marginBottom: 12 }}>
        <div className="backtest-controls">
          <div style={{ display: 'flex', gap: 8, marginRight: 16 }}>
            <button className={`btn ${mode === 'simple' ? 'btn-primary' : ''} btn-sm`}
              onClick={() => setMode('simple')}>单策略回测</button>
            <button className={`btn ${mode === 'comprehensive' ? 'btn-primary' : ''} btn-sm`}
              onClick={handleValidate}>📊 综合验证</button>
          </div>

          {mode === 'comprehensive' && (
            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flex: 1, flexWrap: 'wrap' }}>
              <span style={{ fontSize: 12, color: '#8b8fa3' }}>从</span>
              <div className="control-group">
                <select value={valStart.slice(0,4)} onChange={e => setValStart(e.target.value + valStart.slice(4))}>
                  {Array.from({length:7}, (_,i) => 2020+i).map(y => <option key={y} value={y}>{y}年</option>)}
                </select>
              </div>
              <div className="control-group">
                <select value={valStart.slice(4,6)} onChange={e => { const d=valStart.slice(6,8); setValStart(valStart.slice(0,4)+e.target.value+d); }}>
                  {Array.from({length:12}, (_,i) => String(i+1).padStart(2,'0')).map(m => <option key={m} value={m}>{m}月</option>)}
                </select>
              </div>
              <div className="control-group">
                <select value={valStart.slice(6,8)} onChange={e => setValStart(valStart.slice(0,6)+e.target.value)}>
                  {Array.from({length:31}, (_,i) => String(i+1).padStart(2,'0')).map(d => <option key={d} value={d}>{d}日</option>)}
                </select>
              </div>
              <span style={{ fontSize: 12, color: '#8b8fa3', marginLeft: 4 }}>至</span>
              <div className="control-group">
                <select value={valEnd.slice(0,4)} onChange={e => setValEnd(e.target.value + valEnd.slice(4))}>
                  {Array.from({length:7}, (_,i) => 2020+i).map(y => <option key={y} value={y}>{y}年</option>)}
                </select>
              </div>
              <div className="control-group">
                <select value={valEnd.slice(4,6)} onChange={e => setValEnd(valEnd.slice(0,4)+e.target.value+valEnd.slice(6,8))}>
                  {Array.from({length:12}, (_,i) => String(i+1).padStart(2,'0')).map(m => <option key={m} value={m}>{m}月</option>)}
                </select>
              </div>
              <div className="control-group">
                <select value={valEnd.slice(6,8)} onChange={e => setValEnd(valEnd.slice(0,6)+e.target.value)}>
                  {Array.from({length:31}, (_,i) => String(i+1).padStart(2,'0')).map(d => <option key={d} value={d}>{d}日</option>)}
                </select>
              </div>
              <button className="btn btn-sm" onClick={() => { setValStart(monthsAgo(3)); setValEnd(today()); setTimeout(() => handleValidateRef.current(), 50); }}>近3月</button>
              <button className="btn btn-sm" onClick={() => { setValStart(monthsAgo(6)); setValEnd(today()); setTimeout(() => handleValidateRef.current(), 50); }}>近6月</button>
              <button className="btn btn-sm" onClick={() => { setValStart(yearsAgo(1)); setValEnd(today()); setTimeout(() => handleValidateRef.current(), 50); }}>近1年</button>
              <button className="btn btn-sm" onClick={() => { setValStart(yearsAgo(3)); setValEnd(today()); setTimeout(() => handleValidateRef.current(), 50); }}>近3年</button>
              <button className="btn btn-primary btn-sm" onClick={handleValidate}>▶ 开始验证</button>
            </div>
          )}

          {mode === 'simple' && (
            <>
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
                  <input type="number" step="1" min="1" max="250" value={v}
                    onChange={(e) => handleParamChange(k, e.target.value)} />
                </div>
              ))}
              <div className="control-group" style={{ justifyContent: 'flex-end' }}>
                <button className="btn btn-primary" onClick={handleRun} disabled={loading}>
                  {loading ? '回测中...' : '▶ 开始回测'}
                </button>
              </div>
            </>
          )}
        </div>
      </div>

      {/* ── 综合验证模式 ── */}
      {mode === 'comprehensive' && (
        valLoading ? <div className="loading">⏳ 综合验证中（跑7种策略×多时间段，约需30秒）...</div> :
        validation?.error ? <div className="error-msg">⚠️ {validation.error}</div> :
        validation ? <ComprehensiveResult data={validation} onRunSingle={(s, p) => {
          setStrategy(s); setParams(p); setMode('simple');
          setTimeout(() => onRun({ strategy: s, params: p, start: '20230101', end: today(), initialCapital: 100000 }), 100);
        }} /> : null
      )}

      {/* ── 单策略模式结果 ── */}
      {mode === 'simple' && result && (
        <>
          <div className="backtest-metrics">
            {[{ l: '总收益', v: `${metrics.total_return?.toFixed(1)}%`, c: metrics.total_return >= 0 ? 'green' : 'red' },
              { l: '策略收益', v: `${metrics.total_return?.toFixed(1)}%`, c: metrics.total_return >= 0 ? 'green' : 'red' },
              { l: '买入不动', v: `${metrics.benchmark_return?.toFixed(1)}%`, c: metrics.benchmark_return >= 0 ? 'green' : 'red' },
              { l: 'Sharpe', v: metrics.sharpe_ratio?.toFixed(2) }, { l: '最大跌幅', v: `${metrics.max_drawdown?.toFixed(1)}%`, c: 'red' },
              { l: '胜率', v: `${metrics.win_rate?.toFixed(0)}%` }, { l: '盈亏比', v: metrics.profit_factor?.toFixed(2) },
              { l: '交易次数', v: metrics.total_trades }, { l: '期望值', v: `${metrics.expectancy?.toFixed(2)}%` },
            ].map(m => (
              <div className="card metric-card" key={m.l}>
                <div className={`metric-value ${m.c || ''}`}>{m.v}</div>
                <div className="metric-label">{m.l}</div>
              </div>
            ))}
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
                  <thead><tr><th>日期</th><th>操作</th><th>价格</th><th>股数</th><th>权益</th><th>盈亏%</th></tr></thead>
                  <tbody>
                    {trades.map((t, i) => (
                      <tr key={i}>
                        <td>{t.date}</td>
                        <td className={t.action === 'buy' ? 'buy' : 'sell'}>{t.action === 'buy' ? '买入' : '卖出'}{t.note ? ` (${t.note})` : ''}</td>
                        <td>¥{t.price?.toFixed(2)}</td>
                        <td>{t.shares?.toLocaleString()}</td>
                        <td>¥{t.equity?.toLocaleString()}</td>
                        <td className={t.pnl_pct >= 0 ? 'green' : 'red'}>{t.pnl_pct != null ? `${t.pnl_pct > 0 ? '+' : ''}${t.pnl_pct}%` : '--'}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {trades.length === 0 && (
            <div className="empty-state" style={{ padding: 30, fontSize: 13 }}>该策略在所选时间段内未触发任何交易</div>
          )}
        </>
      )}

      {mode === 'simple' && !result && !loading && (
        <div className="empty-state" style={{ padding: 40 }}>选择策略，点击「开始回测」</div>
      )}
    </div>
  );
}

// ── 综合验证结果展示 ──
function ComprehensiveResult({ data, onRunSingle }) {
  const { strategy_comparison, market_regimes, rolling_validation, parameter_sensitivity } = data;

  const comp = strategy_comparison || {};
  const rolling = rolling_validation || {};
  const windows = rolling.windows || [];
  const sens = parameter_sensitivity || {};

  if (!comp.rankings?.length) {
    return <div className="error-msg">数据不足或时间范围太短（至少需要3个月数据），请选择更长的时间范围</div>;
  }
  const rankOption = {
    backgroundColor: 'transparent',
    grid: { left: 140, right: 20, top: 10, bottom: 25 },
    xAxis: { type: 'value', axisLabel: { color: '#8b8fa3', fontSize: 10, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#1a1d27' } } },
    yAxis: {
      type: 'category',
      data: (comp.rankings || []).map(r => strategyLabel(r.strategy)).reverse(),
      axisLabel: { color: '#8b8fa3', fontSize: 10 },
      axisLine: { lineStyle: { color: '#2a2d3a' } },
    },
    series: [
      {
        name: '策略收益', type: 'bar',
        data: (comp.rankings || []).map(r => r.total_return).reverse(),
        itemStyle: { color: 'rgba(68,138,255,0.8)', borderRadius: [0, 4, 4, 0] },
        barGap: '10%',
      },
      {
        name: '买入不动', type: 'bar',
        data: (comp.rankings || []).map(r => r.benchmark_return).reverse(),
        itemStyle: { color: 'rgba(139,143,163,0.5)', borderRadius: [0, 4, 4, 0] },
      },
    ],
    tooltip: { trigger: 'axis', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 11 } },
    legend: { data: ['策略收益', '买入不动'], bottom: 0, textStyle: { color: '#8b8fa3', fontSize: 10 } },
  };

  // 滚动窗口图表
  const rollOption = {
    backgroundColor: 'transparent',
    grid: { left: 60, right: 20, top: 10, bottom: 25 },
    xAxis: { type: 'category', data: windows.map(w => w.period.slice(0, 10)), axisLabel: { color: '#8b8fa3', fontSize: 9, rotate: 30 }, axisLine: { lineStyle: { color: '#2a2d3a' } } },
    yAxis: { type: 'value', axisLabel: { color: '#8b8fa3', fontSize: 10, formatter: '{value}%' }, splitLine: { lineStyle: { color: '#1a1d27' } } },
    series: [
      { name: '策略收益', type: 'bar', data: windows.map(w => w.strategy_return),
        itemStyle: { color: (p) => p.value >= 0 ? 'rgba(0,200,83,0.6)' : 'rgba(255,61,79,0.6)' } },
    ],
    tooltip: { trigger: 'axis', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 11 } },
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* 1. 策略排名 */}
      <div className="card">
        <div className="card-title">📊 一、7种策略横向排名（在这个时间段内，每种策略各自操作 vs 买入不动）</div>
        {comp.rankings ? (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
              <ReactECharts option={rankOption} style={{ height: 280 }} notMerge lazyUpdate />
              <div style={{ fontSize: 12, maxHeight: 280, overflowY: 'auto' }}>
                <table className="trade-table" style={{ width: '100%' }}>
                  <thead><tr><th>#</th><th>策略</th><th>策略收益</th><th>买入不动</th><th>最大跌幅</th><th>测</th></tr></thead>
                  <tbody>
                    {comp.rankings.map((r) => (
                      <tr key={r.rank} style={r.rank === 1 ? { background: 'rgba(0,200,83,0.08)' } : {}}>
                        <td>{r.rank === 1 ? '🥇' : r.rank === 2 ? '🥈' : r.rank === 3 ? '🥉' : r.rank}</td>
                        <td>{strategyLabel(r.strategy)}</td>
                        <td className={r.total_return >= 0 ? 'green' : 'red'}>{r.total_return > 0 ? '+' : ''}{r.total_return}%</td>
                        <td style={{ color: r.benchmark_return >= 0 ? '#8b8fa3' : '#ff3d4f' }}>{r.benchmark_return > 0 ? '+' : ''}{r.benchmark_return}%</td>
                        <td style={{ color: Math.abs(r.max_drawdown) > 30 ? '#ff3d4f' : '#ffd740' }}>{Math.abs(r.max_drawdown)}%</td>
                        <td><button className="btn btn-sm" onClick={() => onRunSingle(r.strategy, r.params)}>▶</button></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
            <div style={{ marginTop: 12, padding: '10px 14px', background: 'rgba(68,138,255,0.1)', borderRadius: 6, fontSize: 13 }}>
              <strong>🏆 最优策略：{strategyLabel(comp.best_strategy)}</strong>
              <span style={{ marginLeft: 8, color: '#8b8fa3' }}>— {comp.verdict}</span>
              <span style={{ marginLeft: 16, color: '#8b8fa3', fontSize: 12 }}>
                （买入不动 = {data.buy_hold_return > 0 ? '+' : ''}{data.buy_hold_return}%，从{data.first_price}到{data.current_price}）
              </span>
            </div>
          </>
        ) : <div style={{ color: '#8b8fa3', fontSize: 13 }}>数据不足无法排名</div>}
      </div>

      {/* 2. 行情适应性 */}
      <div className="card">
        <div className="card-title">📈 二、不同市场环境表现（牛/熊/震荡，策略赚了多少 vs 不动赚了多少）</div>
        {market_regimes?.segments ? (
          <>
            <div className="backtest-metrics">
              {market_regimes.segments.map((s, i) => (
                <div className="card metric-card" key={i}>
                  <div className="metric-label">{s.regime === 'bull' ? '🐂' : s.regime === 'bear' ? '🐻' : '📊'} {s.label}</div>
                  <div style={{ fontSize: 13 }}>
                    <span className="green">策略+{s.strategy_return}%</span>
                    <span style={{ margin: '0 4px', color: '#8b8fa3' }}>vs</span>
                    <span style={{ color: s.benchmark_return >= 0 ? '#8b8fa3' : '#ff3d4f' }}>不动{s.benchmark_return > 0 ? '+' : ''}{s.benchmark_return}%</span>
                  </div>
                </div>
              ))}
            </div>
            <div style={{ fontSize: 13, padding: '8px 12px', background: 'var(--bg)', borderRadius: 6 }}>
              {Object.entries(market_regimes.summary || {}).filter(([k]) => k !== 'best_regime').map(([k, v]) => (
                <span key={k} style={{ marginRight: 24 }}><strong>{k}</strong>: {v}</span>
              ))}
              <span style={{ color: '#ffd740' }}>👉 {market_regimes.summary?.best_regime}</span>
            </div>
          </>
        ) : <div style={{ color: '#8b8fa3', fontSize: 13 }}>{market_regimes?.message || '数据不足'}</div>}
      </div>

      {/* 3. 滚动窗口 */}
      <div className="card">
        <div className="card-title">🔄 三、滚动窗口 — 用最优策略「{strategyLabel(comp.best_strategy)}」切成多段分别验证，看是不是每次都能赚钱</div>
        {windows.length > 0 ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
            <ReactECharts option={rollOption} style={{ height: 220 }} notMerge lazyUpdate />
            <div style={{ fontSize: 13 }}>
              <div className="backtest-metrics">
                <div className="card metric-card">
                  <div className="metric-value">{rolling.summary?.total_windows}</div>
                  <div className="metric-label">总窗口数</div>
                </div>
                <div className="card metric-card">
                  <div className={`metric-value ${(rolling.summary?.profitable_windows || '').includes('100') ? 'green' : ''}`}>
                    {rolling.summary?.profitable_windows}
                  </div>
                  <div className="metric-label">盈利窗口</div>
                </div>
                <div className="card metric-card">
                  <div className="metric-value">{rolling.summary?.beat_benchmark}</div>
                  <div className="metric-label">跑赢持有</div>
                </div>
                <div className="card metric-card">
                  <div className={`metric-value ${rolling.summary?.stable?.includes('✅') ? 'green' : 'red'}`}>
                    {rolling.summary?.stable}
                  </div>
                  <div className="metric-label">稳定性</div>
                </div>
              </div>
            </div>
          </div>
        ) : <div style={{ color: '#8b8fa3', fontSize: 13 }}>{rolling?.error || '数据不足'}</div>}
      </div>

      {/* 4. 参数敏感性 */}
      <div className="card">
        <div className="card-title">🎛️ 四、参数敏感性 — 对最优策略「{strategyLabel(sens.strategy || comp.best_strategy)}」调参，测结果稳不稳定</div>
        {sens.params_tested ? (
          <>
            <div className="backtest-metrics">
              <div className="card metric-card">
                <div className="metric-label">最优参数</div>
                <div className="metric-value green">{sens.best_param?.params}</div>
                <div className="metric-label">策略收益 {sens.best_param?.total_return > 0 ? '+' : ''}{sens.best_param?.total_return}%</div>
              </div>
              <div className="card metric-card">
                <div className="metric-label">最差参数</div>
                <div className="metric-value red">{sens.worst_param?.params}</div>
                <div className="metric-label">策略收益 {sens.worst_param?.total_return > 0 ? '+' : ''}{sens.worst_param?.total_return}%</div>
              </div>
              <div className="card metric-card">
                <div className="metric-label">所有参数平均</div>
                <div className="metric-value">{sens.mean_excess > 0 ? '+' : ''}{sens.mean_excess}%</div>
                <div className="metric-label">标准差 ±{sens.std_excess}%</div>
              </div>
              <div className="card metric-card">
                <div className="metric-label">参数稳定性</div>
                <div className={`metric-value ${sens.stability?.includes('✅') ? 'green' : 'red'}`} style={{ fontSize: 12 }}>
                  {sens.stability}
                </div>
              </div>
            </div>
          </>
        ) : <div style={{ color: '#8b8fa3', fontSize: 13 }}>数据不足</div>}
      </div>

    </div>
  );
}

function strategyLabel(name) {
  const map = {
    ma_cross: 'MA双均线', macd_signal: 'MACD信号', rsi_mean_rev: 'RSI回归',
    boll_break: '布林突破', boll_mean_rev: '布林回归', triple_screen: '三重滤网', turtle_channel: '海龟通道',
  };
  return map[name] || name;
}
