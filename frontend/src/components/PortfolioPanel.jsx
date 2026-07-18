import { useState, useEffect, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';

const BASE = `http://${window.location.hostname}:8000/api`;

export default function PortfolioPanel({ onStockClick }) {
  const [holdings, setHoldings] = useState([]);
  const [analysis, setAnalysis] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', cost_price: '', quantity: '', notes: '' });
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // 加载持仓和分析
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [hRes, aRes] = await Promise.all([
        fetch(`${BASE}/portfolio`).then(r => r.json()),
        fetch(`${BASE}/portfolio/analyze`).then(r => r.json()),
      ]);
      setHoldings(hRes.holdings || []);
      setAnalysis(aRes.holdings || []);
    } catch (e) {
      console.error(e);
    }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  // 添加持仓
  const handleAdd = async () => {
    if (!form.code || !form.cost_price || !form.quantity) return;
    await fetch(`${BASE}/portfolio/add`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: form.code, name: form.name || form.code,
        cost_price: parseFloat(form.cost_price),
        quantity: parseInt(form.quantity),
        notes: form.notes,
      }),
    });
    setForm({ code: '', name: '', cost_price: '', quantity: '', notes: '' });
    setShowAdd(false);
    load();
  };

  // 删除持仓
  const handleDelete = async (id) => {
    if (!confirm('确认删除这条持仓？')) return;
    await fetch(`${BASE}/portfolio/${id}`, { method: 'DELETE' });
    load();
  };

  // 总览统计
  const totalCost = holdings.reduce((s, h) => s + h.cost_price * h.quantity, 0);
  const totalValue = analysis.reduce((s, a) => s + (a.current_price || 0) * (a.quantity || 0), 0);
  const totalPnl = totalValue - totalCost;
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost * 100) : 0;

  // 持仓饼图
  const pieOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 12 } },
    series: [{
      type: 'pie', radius: ['45%', '70%'], center: ['50%', '55%'],
      label: { color: '#8b8fa3', fontSize: 11 },
      data: analysis.map(a => ({
        name: a.name || a.code,
        value: (a.current_price || 0) * (a.quantity || 0),
      })),
      itemStyle: { borderRadius: 2, borderColor: '#0f1117', borderWidth: 2 },
    }],
  };

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* 总览卡片 */}
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div className="card-title">📋 我的持仓</div>
          <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(!showAdd)}>
            {showAdd ? '取消' : '+ 添加持仓'}
          </button>
        </div>

        {holdings.length > 0 && (
          <div className="metrics-row" style={{ marginTop: 12 }}>
            <div className="card metric-card">
              <div className="metric-value">{holdings.length}</div>
              <div className="metric-label">持仓数量</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value">¥{totalCost.toLocaleString()}</div>
              <div className="metric-label">持仓成本</div>
            </div>
            <div className="card metric-card">
              <div className="metric-value">¥{totalValue.toLocaleString()}</div>
              <div className="metric-label">当前市值</div>
            </div>
            <div className="card metric-card">
              <div className={`metric-value ${totalPnl >= 0 ? 'green' : 'red'}`}>
                {totalPnl >= 0 ? '+' : ''}¥{totalPnl.toLocaleString()}
              </div>
              <div className="metric-label">浮动盈亏</div>
            </div>
            <div className="card metric-card">
              <div className={`metric-value ${totalPnlPct >= 0 ? 'green' : 'red'}`}>
                {totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%
              </div>
              <div className="metric-label">收益率</div>
            </div>
            <div className="card metric-card">
              <button className="btn btn-sm" onClick={load} disabled={loading}>
                {loading ? '...' : '🔄 刷新'}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 添加持仓表单 */}
      {showAdd && (
        <div className="card">
          <div className="card-title">添加新持仓</div>
          <div style={{ position: 'relative', marginTop: 8 }}>
            <input className="search-input" style={{ width: '100%' }}
              placeholder="输入股票名称或代码搜索 — 如：平安银行、000001、通信ETF"
              value={searching ? undefined : (form.name ? `${form.code} ${form.name}` : '')}
              onChange={async (e) => {
                const kw = e.target.value;
                setSearching(true);
                setForm({ ...form, code: '', name: '' });
                if (kw.trim().length < 2) { setSearchResults([]); return; }
                try {
                  const r = await fetch(`${BASE}/stock/search?keyword=${encodeURIComponent(kw)}`);
                  const d = await r.json();
                  setSearchResults((d.results || []).slice(0, 10));
                } catch { setSearchResults([]); }
              }}
              onFocus={() => { setSearching(true); }}
            />
            {searching && searchResults.length > 0 && (
              <div className="search-dropdown" style={{ position: 'absolute', zIndex: 10, width: '100%' }}>
                {searchResults.map((r) => (
                  <div key={r.code} className="search-item"
                    onClick={() => {
                      setForm({ ...form, code: r.code, name: r.name });
                      setSearchResults([]);
                      setSearching(false);
                    }}>
                    <span className="code">{r.code}</span>
                    <span className="name" style={{ marginLeft: 8 }}>{r.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          {form.code && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
              <div>
                <label style={{ fontSize:11, color:'#8b8fa3' }}>已选股票</label>
                <div style={{ fontSize:14, fontWeight:600 }}>{form.code} {form.name}</div>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <input className="search-input" type="number" step="0.01" placeholder="成本价 *" value={form.cost_price}
                  onChange={e => setForm({ ...form, cost_price: e.target.value })} />
                <input className="search-input" type="number" placeholder="数量(股) *" value={form.quantity}
                  onChange={e => setForm({ ...form, quantity: e.target.value })} />
              </div>
            </div>
          )}
          <div style={{ marginTop: 8 }}>
            <input className="search-input" style={{ width: '100%' }} placeholder="备注（可选）" value={form.notes}
              onChange={e => setForm({ ...form, notes: e.target.value })} />
          </div>
          <button className="btn btn-primary" style={{ marginTop: 8 }} onClick={handleAdd} disabled={!form.code}>
            确认添加
          </button>
        </div>
      )}

      {/* 持仓分析列表 */}
      {analysis.length > 0 ? (
        <>
          {/* 饼图 */}
          <div className="card">
            <div className="card-title">持仓分布</div>
            <ReactECharts option={pieOption} style={{ height: 240 }} notMerge lazyUpdate />
          </div>

          {/* 逐个持仓分析 */}
          {analysis.map((a) => (
            <div key={a.holding_id} className="card" style={{ cursor: 'pointer' }}
              onClick={() => onStockClick?.(a.code)}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
                    <span style={{ fontSize: 16, fontWeight: 700 }}>{a.name || a.code}</span>
                    <span style={{ color: '#8b8fa3', fontFamily: 'monospace', fontSize: 12 }}>{a.code}</span>
                    <span className={`signal-badge ${a.signal}`}>
                      {a.signal === 'buy' ? '买入' : a.signal === 'sell' ? '卖出' : '持有'}
                    </span>
                    <span style={{ fontSize: 11, color: '#8b8fa3' }}>
                      {a.confidence === 'high' ? '★★★' : a.confidence === 'medium' ? '★★☆' : '★☆☆'}
                    </span>
                  </div>

                  {/* 价格信息 */}
                  <div style={{ display: 'flex', gap: 24, marginTop: 8, fontSize: 13 }}>
                    <div>
                      <span style={{ color: '#8b8fa3' }}>现价 </span>
                      <strong>¥{a.current_price}</strong>
                    </div>
                    {a.cost_price > 0 && (
                      <>
                        <div>
                          <span style={{ color: '#8b8fa3' }}>成本 </span>
                          <span>¥{a.cost_price}</span>
                        </div>
                        <div>
                          <span style={{ color: '#8b8fa3' }}>盈亏 </span>
                          <span style={{ color: a.pnl_pct >= 0 ? '#00c853' : '#ff3d4f', fontWeight: 600 }}>
                            {a.pnl_pct >= 0 ? '+' : ''}{a.pnl_pct}%
                          </span>
                        </div>
                      </>
                    )}
                    <div>
                      <span style={{ color: '#8b8fa3' }}>持有 </span>
                      <span>{a.quantity} 股</span>
                    </div>
                    <div>
                      <span style={{ color: '#8b8fa3' }}>市值 </span>
                      <span>¥{((a.current_price || 0) * (a.quantity || 0)).toLocaleString()}</span>
                    </div>
                  </div>

                  {/* 买卖区间 */}
                  <div style={{ display: 'flex', gap: 20, marginTop: 10 }}>
                    <div style={{ background: 'rgba(0,200,83,0.08)', borderRadius: 6, padding: '8px 14px', flex: 1 }}>
                      <div style={{ fontSize: 11, color: '#8b8fa3', marginBottom: 2 }}>🟢 建议买入区间</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#00c853' }}>
                        ¥{a.buy_zone?.low} ~ ¥{a.buy_zone?.high}
                      </div>
                      <div style={{ fontSize: 11, color: '#8b8fa3' }}>{a.buy_zone?.label}</div>
                    </div>
                    <div style={{ background: 'rgba(255,61,79,0.08)', borderRadius: 6, padding: '8px 14px', flex: 1 }}>
                      <div style={{ fontSize: 11, color: '#8b8fa3', marginBottom: 2 }}>🔴 建议卖出区间</div>
                      <div style={{ fontSize: 15, fontWeight: 700, color: '#ff3d4f' }}>
                        ¥{a.sell_zone?.low} ~ ¥{a.sell_zone?.high}
                      </div>
                      <div style={{ fontSize: 11, color: '#8b8fa3' }}>{a.sell_zone?.label}</div>
                    </div>
                  </div>

                  {/* 技术信号 */}
                  <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: 12, flexWrap: 'wrap' }}>
                    {a.ma_trend && <span style={{ color: a.ma_trend.includes('多') ? '#00c853' : '#ff3d4f' }}>📊 {a.ma_trend}</span>}
                    {a.macd_signal && <span style={{ color: a.macd_signal.includes('金叉') ? '#00c853' : '#ff3d4f' }}>📈 {a.macd_signal}</span>}
                    {a.rsi_signal && <span style={{ color: a.rsi_signal.includes('超卖') ? '#00c853' : '#ff3d4f' }}>📉 {a.rsi_signal}</span>}
                    {a.boll_signal && <span style={{ color: '#ffd740' }}>📏 {a.boll_signal}</span>}
                  </div>

                  {/* 理由和风险 */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
                    <div>
                      {a.reasons?.map((r, i) => (
                        <div key={i} style={{ fontSize: 12, color: '#8b8fa3', padding: '2px 0' }}>✅ {r}</div>
                      ))}
                    </div>
                    <div>
                      {a.risks?.map((r, i) => (
                        <div key={i} style={{ fontSize: 12, color: '#ff3d4f', padding: '2px 0' }}>⚠️ {r}</div>
                      ))}
                    </div>
                  </div>

                  {/* 止盈止损 */}
                  <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
                    <div className="price-target">
                      <div className="label">🛑 止损</div>
                      <div className="value stop">¥{a.stop_loss}</div>
                    </div>
                    <div className="price-target">
                      <div className="label">🎯 止盈</div>
                      <div className="value take">¥{a.take_profit}</div>
                    </div>
                  </div>
                </div>

                <button className="btn btn-sm" style={{ color: '#ff3d4f' }}
                  onClick={(e) => { e.stopPropagation(); handleDelete(a.holding_id); }}>
                  ✕ 删除
                </button>
              </div>
            </div>
          ))}
        </>
      ) : (
        <div className="empty-state" style={{ padding: 40 }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>📋</div>
          <div>还没有持仓记录</div>
          <div className="hint">点击「+ 添加持仓」输入你的股票代码、成本价和数量</div>
        </div>
      )}
    </div>
  );
}
