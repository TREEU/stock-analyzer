import { useState } from 'react';
import StockSearch from './components/StockSearch';
import PriceChart from './components/PriceChart';
import KeyMetricsBar from './components/KeyMetricsBar';
import TechPanel from './components/TechPanel';
import ValuationPanel from './components/ValuationPanel';
import RiskPanel from './components/RiskPanel';
import BacktestPanel from './components/BacktestPanel';
import RecPanel from './components/RecPanel';
import MarketOverview from './components/MarketOverview';
import PortfolioPanel from './components/PortfolioPanel';
import { useAnalysis } from './hooks/useAnalysis';

const TABS = [
  { key: 'rec', label: '操作建议' },
  { key: 'tech', label: '技术指标' },
  { key: 'valuation', label: '估值分析' },
  { key: 'risk', label: '风险评估' },
  { key: 'backtest', label: '策略回测' },
];

export default function App() {
  const [tab, setTab] = useState('portfolio');
  const {
    code, setCode, loading, error, data,
    backtestResult, backtestLoading, executeBacktest, strategies,
  } = useAnalysis();

  return (
    <>
      <header className="app-header">
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          {code && (
            <button className="btn btn-sm" onClick={() => { setCode(''); setTab('rec'); }}
              style={{ background: 'var(--bg)', border: '1px solid var(--border)', color: '#8b8fa3', cursor: 'pointer' }}>
              ← 返回持仓
            </button>
          )}
          <h1>A股量化分析平台</h1>
          <nav style={{ display: 'flex', gap: 4, marginLeft: 16 }}>
            {[
              { id: 'market', label: '行情' },
              { id: 'portfolio', label: '持仓' },
            ].map(n => (
              <a key={n.id} href={`#${n.id}`} style={{
                padding: '3px 10px', borderRadius: 4, fontSize: 12, color: '#8b8fa3',
                textDecoration: 'none', background: 'var(--bg)', border: '1px solid var(--border)',
              }} onClick={(e) => {
                e.preventDefault();
                const el = document.getElementById(n.id);
                if (el) el.scrollIntoView({ behavior: 'smooth' });
                // 如果在分析页，点持仓就回到首页
                if (n.id === 'portfolio' && code) setCode('');
              }}>{n.label}</a>
            ))}
          </nav>
        </div>
        <StockSearch value={code} onChange={setCode} />
      </header>

      <main className="app-main">
        {error && <div className="error-msg"> {error}</div>}

        {!code && !loading && (
          <>
            <div id="market"><MarketOverview onStockClick={(c) => { setCode(c); setTab('rec'); }} /></div>
            <div id="portfolio"><PortfolioPanel onStockClick={(c) => { setCode(c); setTab('rec'); }} /></div>
          </>
        )}

        {loading && <div className="loading">加载数据中...</div>}

        {data && !loading && (
          <>
            {/* 信息卡片 + K线图 */}
            <div className="top-grid">
              <div className="card info-card">
                <div className="stock-name">{data.name}</div>
                <div className="stock-code">{data.code}</div>
                <div style={{ marginTop: 12 }}>
                  <div className="info-row">
                    <span className="label">现价</span>
                    <span className="value">
                      {data.stock_info?.latest_price?.toFixed(2) || '--'}
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="label">PE(TTM)</span>
                    <span className="value">
                      {data.valuation?.pe_ttm > 0 ? data.valuation.pe_ttm.toFixed(1) : '--'}
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="label">PB</span>
                    <span className="value">
                      {data.valuation?.pb > 0 ? data.valuation.pb.toFixed(2) : '--'}
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="label">市值</span>
                    <span className="value">
                      {data.stock_info?.market_cap > 0
                        ? (data.stock_info.market_cap / 1e8).toFixed(0) + '亿'
                        : '--'}
                    </span>
                  </div>
                  <div className="info-row">
                    <span className="label">换手率</span>
                    <span className="value">
                      {data.stock_info?.turnover_rate > 0
                        ? data.stock_info.turnover_rate.toFixed(2) + '%'
                        : '--'}
                    </span>
                  </div>
                </div>
              </div>

              <PriceChart
                priceData={data.price_data || []}
                indicators={data.indicators?.data || []}
                height={340}
              />

              <div />
            </div>

            <KeyMetricsBar
              stockInfo={data.stock_info}
              indicators={data.indicators}
              risk={data.risk}
            />

            {/* Tab 栏 */}
            <div className="tab-bar">
              {TABS.map((t) => (
                <button
                  key={t.key}
                  className={`tab-btn ${tab === t.key ? 'active' : ''}`}
                  onClick={() => setTab(t.key)}
                >
                  {t.label}
                </button>
              ))}
            </div>

            {/* Tab 内容 */}
            {tab === 'tech' && (
              <TechPanel indicators={data.indicators} />
            )}
            {tab === 'valuation' && (
              <ValuationPanel
                valuation={data.valuation}
                stockInfo={data.stock_info}
              />
            )}
            {tab === 'risk' && (
              <RiskPanel risk={data.risk} priceData={data.price_data} />
            )}
            {tab === 'backtest' && (
              <BacktestPanel
                code={code}
                strategies={strategies}
                onRun={executeBacktest}
                result={backtestResult}
                loading={backtestLoading}
              />
            )}
            {tab === 'rec' && (
              <RecPanel recommendation={data.recommendation} />
            )}
          </>
        )}
      </main>
    </>
  );
}
