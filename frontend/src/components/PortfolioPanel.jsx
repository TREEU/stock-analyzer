import { useState, useEffect, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';

const BASE = `http://${window.location.hostname}:8000/api`;

function HoldingCard({ a, onStockClick, onDelete, onEdit }) {
  const [editing, setEditing] = useState(false);
  const [editForm, setEditForm] = useState({ cost_price: a.cost_price || '', quantity: a.quantity || '', notes: a.notes || '' });

  const save = () => {
    onEdit(a.holding_id, { cost_price: parseFloat(editForm.cost_price), quantity: parseInt(editForm.quantity), notes: editForm.notes });
    setEditing(false);
  };

  if (editing) {
    return (
      <div className="card">
        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 8 }}>
          <span style={{ fontWeight: 600 }}>{a.name || a.code}</span>
          <span style={{ color: '#8b8fa3', fontSize: 12 }}>{a.code}</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr auto', gap: 8, alignItems: 'end' }}>
          <div className="control-group">
            <label>成本价</label>
            <input type="number" step="0.01" value={editForm.cost_price}
              onChange={e => setEditForm({ ...editForm, cost_price: e.target.value })} />
          </div>
          <div className="control-group">
            <label>数量</label>
            <input type="number" value={editForm.quantity}
              onChange={e => setEditForm({ ...editForm, quantity: e.target.value })} />
          </div>
          <div className="control-group">
            <label>备注</label>
            <input value={editForm.notes} onChange={e => setEditForm({ ...editForm, notes: e.target.value })} />
          </div>
          <div style={{ display: 'flex', gap: 4 }}>
            <button className="btn btn-primary btn-sm" onClick={save}>保存</button>
            <button className="btn btn-sm" onClick={() => setEditing(false)}>取消</button>
          </div>
        </div>
      </div>
    );
  }
  return (
    <div className="card" style={{ cursor: 'pointer' }} onClick={() => onStockClick?.(a.code)}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <div style={{ flex: 1 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
            <span style={{ fontSize: 16, fontWeight: 700 }}>{a.name || a.code}</span>
            <span style={{ color: '#8b8fa3', fontFamily: 'monospace', fontSize: 12 }}>{a.code}</span>
            <span className={`signal-badge ${a.signal}`}>
              {a.signal === 'buy' ? '买入' : a.signal === 'sell' ? '卖出' : '持有'}
            </span>
            <span style={{ fontSize: 10, color: '#8b8fa3' }}>技术面综合判断</span>
          </div>

          <div style={{ display: 'flex', gap: 24, marginTop: 8, fontSize: 13 }}>
            <div><span style={{ color: '#8b8fa3' }}>现价 </span><strong>¥{a.current_price}</strong></div>
            {a.cost_price > 0 && (
              <>
                <div><span style={{ color: '#8b8fa3' }}>成本 </span><span>¥{a.cost_price}</span></div>
                <div>
                  <span style={{ color: '#8b8fa3' }}>盈亏 </span>
                  <span style={{ color: a.pnl_pct >= 0 ? '#00c853' : '#ff3d4f', fontWeight: 600 }}>
                    {a.pnl_pct >= 0 ? '+' : ''}{a.pnl_pct}%
                  </span>
                </div>
              </>
            )}
            <div><span style={{ color: '#8b8fa3' }}>持有 </span><span>{a.quantity} 股</span></div>
            <div><span style={{ color: '#8b8fa3' }}>市值 </span><span>¥{((a.current_price || 0) * (a.quantity || 0)).toLocaleString()}</span></div>
          </div>

          <div style={{ display: 'flex', gap: 20, marginTop: 10 }}>
            <div style={{ background: 'rgba(0,200,83,0.08)', borderRadius: 6, padding: '8px 14px', flex: 1 }}>
              <div style={{ fontSize: 11, color: '#8b8fa3', marginBottom: 2 }}>🟢 建议买入区间</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#00c853' }}>¥{a.buy_zone?.low} ~ ¥{a.buy_zone?.high}</div>
              <div style={{ fontSize: 11, color: '#8b8fa3' }}>{a.buy_zone?.label}</div>
            </div>
            <div style={{ background: 'rgba(255,61,79,0.08)', borderRadius: 6, padding: '8px 14px', flex: 1 }}>
              <div style={{ fontSize: 11, color: '#8b8fa3', marginBottom: 2 }}>🔴 建议卖出区间</div>
              <div style={{ fontSize: 15, fontWeight: 700, color: '#ff3d4f' }}>¥{a.sell_zone?.low} ~ ¥{a.sell_zone?.high}</div>
              <div style={{ fontSize: 11, color: '#8b8fa3' }}>{a.sell_zone?.label}</div>
            </div>
          </div>

          <div style={{ display: 'flex', gap: 12, marginTop: 8, fontSize: 12, flexWrap: 'wrap' }}>
            {a.ma_trend && <span style={{ color: a.ma_trend.includes('多') ? '#00c853' : '#ff3d4f' }}>📊 {a.ma_trend}</span>}
            {a.macd_signal && <span style={{ color: a.macd_signal.includes('金叉') ? '#00c853' : '#ff3d4f' }}>📈 {a.macd_signal}</span>}
            {a.rsi_signal && <span style={{ color: a.rsi_signal.includes('超卖') ? '#00c853' : '#ff3d4f' }}>📉 {a.rsi_signal}</span>}
            {a.boll_signal && <span style={{ color: '#ffd740' }}>📏 {a.boll_signal}</span>}
          </div>

          <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
            {a.reasons?.slice(0, 3).map((r, i) => (
              <span key={i} style={{ fontSize: 12, color: '#8b8fa3' }}>✅ {r}</span>
            ))}
          </div>

          <div style={{ display: 'flex', gap: 16, marginTop: 8 }}>
            <div className="price-target"><div className="label">🛑 止损</div><div className="value stop">¥{a.stop_loss}</div></div>
            <div className="price-target"><div className="label">🎯 止盈</div><div className="value take">¥{a.take_profit}</div></div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 4 }}>
          <button className="btn btn-sm" style={{ color: '#8b8fa3' }}
            onClick={(e) => { e.stopPropagation(); setEditing(true); }}>✎ 编辑</button>
          <button className="btn btn-sm" style={{ color: '#ff3d4f' }}
            onClick={(e) => { e.stopPropagation(); onDelete(a.holding_id); }}>✕ 删除</button>
        </div>
      </div>
    </div>
  );
}

export default function PortfolioPanel({ onStockClick }) {
  const [holdings, setHoldings] = useState([]);
  const [analysis, setAnalysis] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [form, setForm] = useState({ code: '', name: '', cost_price: '', quantity: '', notes: '' });
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [sortBy, setSortBy] = useState('signal');

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [hRes, aRes] = await Promise.all([
        fetch(`${BASE}/portfolio`).then(r => r.json()),
        fetch(`${BASE}/portfolio/analyze`).then(r => r.json()),
      ]);
      setHoldings(hRes.holdings || []);
      setAnalysis(aRes.holdings || []);
    } catch (e) { console.error(e); }
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);
  useEffect(() => { const t = setInterval(load, 30000); return () => clearInterval(t); }, [load]);

  const handleAdd = async () => {
    if (!form.code || !form.cost_price || !form.quantity) return;
    await fetch(`${BASE}/portfolio/add`, {
      method: 'POST', headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ code: form.code, name: form.name || form.code, cost_price: parseFloat(form.cost_price), quantity: parseInt(form.quantity), notes: form.notes }),
    });
    setForm({ code: '', name: '', cost_price: '', quantity: '', notes: '' });
    setShowAdd(false);
    load();
  };

  const handleDelete = async (id) => {
    if (!confirm('确认删除这条持仓？')) return;
    await fetch(`${BASE}/portfolio/${id}`, { method: 'DELETE' });
    load();
  };

  const handleEdit = async (id, data) => {
    await fetch(`${BASE}/portfolio/${id}?cost_price=${data.cost_price}&quantity=${data.quantity}&notes=${encodeURIComponent(data.notes||'')}`, { method: 'PUT' });
    load();
  };

  const totalCost = holdings.reduce((s, h) => s + h.cost_price * h.quantity, 0);
  const totalValue = analysis.reduce((s, a) => s + (a.current_price || 0) * (a.quantity || 0), 0);
  const totalPnl = totalValue - totalCost;
  const totalPnlPct = totalCost > 0 ? (totalPnl / totalCost * 100) : 0;

  const sortedAnalysis = [...analysis].sort((a, b) => {
    if (sortBy === 'value') { const va = (a.current_price || 0) * (a.quantity || 0); const vb = (b.current_price || 0) * (b.quantity || 0); return vb - va; }
    if (sortBy === 'pnl') return (b.pnl_pct || 0) - (a.pnl_pct || 0);
    const order = { buy: 0, hold: 1, sell: 2 };
    return (order[a.signal] || 1) - (order[b.signal] || 1);
  });

  const pieOption = {
    backgroundColor: 'transparent',
    tooltip: { trigger: 'item', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 12 } },
    series: [{ type: 'pie', radius: ['45%', '70%'], center: ['50%', '55%'], label: { color: '#8b8fa3', fontSize: 11 },
      data: sortedAnalysis.map(a => ({ name: a.name || a.code, value: (a.current_price || 0) * (a.quantity || 0) })),
      itemStyle: { borderRadius: 2, borderColor: '#0f1117', borderWidth: 2 },
    }],
  };

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      <div className="card">
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
            <div className="card-title" style={{ margin: 0 }}>📋 我的持仓</div>
            <span style={{ fontSize: 11, color: '#8b8fa3' }}>排序:</span>
            {[{ k: 'signal', l: '信号' }, { k: 'value', l: '市值' }, { k: 'pnl', l: '盈亏' }].map(s => (
              <button key={s.k} className={`btn btn-sm ${sortBy === s.k ? 'btn-primary' : ''}`}
                style={sortBy !== s.k ? { background: 'var(--bg)', border: '1px solid var(--border)', color: '#8b8fa3' } : {}}
                onClick={() => setSortBy(s.k)}>{s.l}</button>
            ))}
          </div>
          <button className="btn btn-primary btn-sm" onClick={() => setShowAdd(!showAdd)}>{showAdd ? '取消' : '+ 添加持仓'}</button>
        </div>

        {holdings.length > 0 && (
          <div className="metrics-row" style={{ marginTop: 12 }}>
            <div className="card metric-card"><div className="metric-value">{holdings.length}</div><div className="metric-label">持仓数量</div></div>
            <div className="card metric-card"><div className="metric-value">¥{totalCost.toLocaleString()}</div><div className="metric-label">持仓成本</div></div>
            <div className="card metric-card"><div className="metric-value">¥{totalValue.toLocaleString()}</div><div className="metric-label">当前市值</div></div>
            <div className="card metric-card"><div className={`metric-value ${totalPnl >= 0 ? 'green' : 'red'}`}>{totalPnl >= 0 ? '+' : ''}¥{totalPnl.toLocaleString()}</div><div className="metric-label">浮动盈亏</div></div>
            <div className="card metric-card"><div className={`metric-value ${totalPnlPct >= 0 ? 'green' : 'red'}`}>{totalPnlPct >= 0 ? '+' : ''}{totalPnlPct.toFixed(2)}%</div><div className="metric-label">收益率</div></div>
            <div className="card metric-card"><button className="btn btn-sm" onClick={load} disabled={loading}>{loading ? '...' : '🔄 刷新'}</button></div>
          </div>
        )}
      </div>

      {showAdd && (
        <div className="card">
          <div className="card-title">添加新持仓</div>
          <div style={{ position: 'relative', marginTop: 8 }}>
            <input className="search-input" style={{ width: '100%' }}
              placeholder="输入股票名称或代码搜索"
              onChange={async (e) => {
                const kw = e.target.value; setSearching(true);
                if (kw.trim().length < 2) { setSearchResults([]); return; }
                if (/^\d{6}$/.test(kw.trim())) { setForm({ ...form, code: kw.trim(), name: kw.trim() }); setSearchResults([{ code: kw.trim(), name: kw.trim() }]); return; }
                try { const r = await fetch(`${BASE}/stock/search?keyword=${encodeURIComponent(kw)}`); const d = await r.json(); setSearchResults((d.results || []).slice(0, 10)); } catch { setSearchResults([]); }
              }}
            />
            {searching && searchResults.length > 0 && (
              <div className="search-dropdown" style={{ position: 'absolute', zIndex: 10, width: '100%' }}>
                {searchResults.map((r) => (
                  <div key={r.code} className="search-item" onClick={() => { setForm({ ...form, code: r.code, name: r.name }); setSearchResults([]); setSearching(false); }}>
                    <span className="code">{r.code}</span><span className="name" style={{ marginLeft: 8 }}>{r.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          {form.code && (
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8, marginTop: 8 }}>
              <div><label style={{ fontSize: 11, color: '#8b8fa3' }}>已选股票</label><div style={{ fontSize: 14, fontWeight: 600 }}>{form.code} {form.name}</div></div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
                <input className="search-input" type="number" step="0.01" placeholder="成本价 *" value={form.cost_price} onChange={e => setForm({ ...form, cost_price: e.target.value })} />
                <input className="search-input" type="number" placeholder="数量(股) *" value={form.quantity} onChange={e => setForm({ ...form, quantity: e.target.value })} />
              </div>
            </div>
          )}
          <div style={{ marginTop: 8 }}><input className="search-input" style={{ width: '100%' }} placeholder="备注（可选）" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></div>
          <button className="btn btn-primary" style={{ marginTop: 8 }} onClick={handleAdd} disabled={!form.code}>确认添加</button>
        </div>
      )}

      {sortedAnalysis.length > 0 && (
        <div className="card" style={{ background: 'rgba(68,138,255,0.06)', border: '1px solid rgba(68,138,255,0.2)' }}>
          <div style={{ fontSize: 12, color: '#8b8fa3', lineHeight: 1.8 }}>
            <span style={{ color: '#448aff', fontWeight: 600 }}>💡 使用说明</span><br />
            <strong>持仓信号</strong> = 实时技术面打分，回答「现在该买还是卖？」<br />
            <strong>策略回测</strong> = 历史数据跑策略，回答「什么方法最赚钱？」<br />
            <span style={{ color: '#448aff' }}>👉 正确用法：点股票 → 策略回测 → 找到最优策略 → 回持仓看信号 → 按策略执行</span>
          </div>
        </div>
      )}

      {sortedAnalysis.length > 0 && (
        <div className="card">
          <div className="card-title">持仓分布</div>
          <ReactECharts option={pieOption} style={{ height: 240 }} notMerge lazyUpdate />
        </div>
      )}

      {sortedAnalysis.map((a) => (
        <HoldingCard key={a.holding_id} a={a} onStockClick={onStockClick} onDelete={handleDelete} onEdit={handleEdit} />
      ))}

      {!analysis.length && !loading && (
        <div className="empty-state" style={{ padding: 40 }}>
          <div style={{ fontSize: 36, marginBottom: 8 }}>📋</div>
          <div>还没有持仓记录</div>
          <div className="hint">点击「+ 添加持仓」输入你的股票代码、成本价和数量</div>
        </div>
      )}
    </div>
  );
}
