import { useState, useEffect, useCallback } from 'react';
import ReactECharts from 'echarts-for-react';

async function fetchOverview() {
  const BASE = 'http://localhost:8000/api';
  const [indices, flow] = await Promise.all([
    fetch(`${BASE}/market/overview`).then(r => r.json()).catch(() => ({})),
    fetch(`${BASE}/market/sector-flow`).then(r => r.json()).catch(() => ({ data: [] })),
  ]);
  return { indices, flow: flow.data || [] };
}

export default function MarketOverview({ onStockClick }) {
  const [data, setData] = useState({ indices: {}, flow: [] });
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [showDropdown, setShowDropdown] = useState(false);
  const [lastUpdate, setLastUpdate] = useState('');

  const refresh = useCallback(async () => {
    const d = await fetchOverview();
    setData(d);
    setLastUpdate(new Date().toLocaleTimeString());
  }, []);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 10000); // 10秒刷新
    return () => clearInterval(timer);
  }, [refresh]);

  // 实时搜索
  const handleSearch = useCallback(async (kw) => {
    setSearchKeyword(kw);
    if (kw.trim().length < 2) { setSearchResults([]); setShowDropdown(false); return; }
    try {
      const r = await fetch(`http://localhost:8000/api/market/search-realtime?keyword=${encodeURIComponent(kw)}`);
      const d = await r.json();
      setSearchResults(d.results || []);
      setShowDropdown((d.results || []).length > 0);
    } catch { setSearchResults([]); }
  }, []);

  // 板块资金流向图
  const flowOption = {
    backgroundColor: 'transparent',
    grid: { left: 100, right: 10, top: 5, bottom: 5 },
    xAxis: { type: 'value', axisLabel: { color: '#8b8fa3', fontSize: 10, formatter: '{value}亿' }, splitLine: { lineStyle: { color: '#1a1d27' } } },
    yAxis: { type: 'category', data: (data.flow || []).map(f => f.name).reverse(), axisLabel: { color: '#8b8fa3', fontSize: 10, width: 90, overflow: 'truncate' }, axisLine: { lineStyle: { color: '#2a2d3a' } } },
    series: [{
      type: 'bar',
      data: (data.flow || []).map(f => (f.net_inflow / 1e8).toFixed(2)).reverse(),
      itemStyle: { color: (p) => p.value >= 0 ? 'rgba(0,200,83,0.7)' : 'rgba(255,61,79,0.7)' },
      label: { show: true, position: 'right', fontSize: 10, color: '#8b8fa3', formatter: '{c}' },
    }],
    tooltip: { trigger: 'axis', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 11 } },
  };

  return (
    <div className="panel" style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* 实时搜索栏 */}
      <div className="card" style={{ padding: '12px 16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 13, fontWeight: 600, whiteSpace: 'nowrap' }}>🔍 实时搜索</span>
          <div style={{ position: 'relative', flex: 1 }}>
            <input
              className="search-input" style={{ width: '100%' }}
              placeholder="输代码或名称搜实时行情..."
              value={searchKeyword}
              onChange={(e) => handleSearch(e.target.value)}
              onFocus={() => searchResults.length > 0 && setShowDropdown(true)}
            />
            {showDropdown && (
              <div className="search-dropdown">
                {searchResults.map((r) => (
                  <div key={r.code} className="search-item"
                    style={{ justifyContent: 'space-between', cursor: 'pointer' }}
                    onClick={() => { onStockClick?.(r.code); setShowDropdown(false); setSearchKeyword(''); }}>
                    <div>
                      <span className="code">{r.code}</span>
                      <span className="name" style={{ marginLeft: 8 }}>{r.name}</span>
                    </div>
                    <div style={{ textAlign: 'right' }}>
                      <span style={{ fontWeight: 600, color: r.pct_change >= 0 ? '#00c853' : '#ff3d4f' }}>
                        ¥{r.price?.toFixed(2) || '--'}
                      </span>
                      <span style={{ marginLeft: 8, fontSize: 12, color: r.pct_change >= 0 ? '#00c853' : '#ff3d4f' }}>
                        {r.pct_change > 0 ? '+' : ''}{r.pct_change?.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 三大指数 + 板块资金 */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        {/* 三大指数卡片 */}
        <div className="card">
          <div className="card-title">三大指数</div>
          <div style={{ display: 'flex', gap: 8, flexDirection: 'column' }}>
            {Object.entries(data.indices).map(([name, idx]) => (
              <div key={name} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '10px 12px', background: 'var(--bg)', borderRadius: 6 }}>
                <div>
                  <div style={{ fontSize: 14, fontWeight: 600 }}>{name}</div>
                  <div style={{ fontSize: 20, fontWeight: 700, marginTop: 2 }}>{idx.price?.toFixed(2)}</div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: idx.pct_change >= 0 ? '#00c853' : '#ff3d4f' }}>
                    {idx.change >= 0 ? '+' : ''}{idx.change?.toFixed(2)}
                  </div>
                  <div style={{
                    fontSize: 16, fontWeight: 700, padding: '2px 10px', borderRadius: 4,
                    background: idx.pct_change >= 0 ? 'rgba(0,200,83,0.15)' : 'rgba(255,61,79,0.15)',
                    color: idx.pct_change >= 0 ? '#00c853' : '#ff3d4f',
                  }}>
                    {idx.pct_change >= 0 ? '+' : ''}{idx.pct_change?.toFixed(2)}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* 板块资金流向 */}
        <div className="card">
          <div className="card-title">行业资金流向 Top10</div>
          {data.flow.length > 0 ? (
            <ReactECharts option={flowOption} style={{ height: 280 }} notMerge lazyUpdate />
          ) : (
            <div style={{ padding: 40, textAlign: 'center', color: '#8b8fa3' }}>数据加载中...</div>
          )}
        </div>
      </div>

      <div style={{ textAlign: 'right', fontSize: 11, color: '#8b8fa3' }}>
        更新于 {lastUpdate} · 每10秒自动刷新
        <button className="btn btn-sm" style={{ marginLeft: 8 }} onClick={refresh}>🔄 手动刷新</button>
      </div>
    </div>
  );
}
