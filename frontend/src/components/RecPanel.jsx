export default function RecPanel({ recommendation }) {
  if (!recommendation) return null;

  const rec = recommendation;
  const score = rec.total_score || 0;
  const signal = rec.signal || 'hold';
  const confidence = rec.confidence || 'low';

  const scoreColor =
    score >= 60 ? '#00c853' :
    score >= 40 ? '#ffd740' : '#ff3d4f';

  return (
    <div className="panel">
      <div className="rec-header">
        <div className="score-circle" style={{ borderColor: scoreColor, color: scoreColor }}>
          {score.toFixed(0)}
        </div>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
            <span className={`signal-badge ${signal}`}>
              {signal === 'buy' ? '🟢 买入' : signal === 'sell' ? '🔴 卖出' : '🟡 持有'}
            </span>
            <span style={{ fontSize: 13, color: '#8b8fa3' }}>
              置信度: {confidence === 'high' ? '高' : confidence === 'medium' ? '中' : '低'}
            </span>
          </div>
          <div style={{ marginTop: 8, fontSize: 14, color: '#e1e4ed' }}>
            建议仓位：<strong>{rec.position_pct}%</strong>
          </div>
        </div>
      </div>

      {/* 评分明细 */}
      <div className="backtest-metrics" style={{ marginBottom: 16 }}>
        {[
          { label: '趋势', value: rec.trend_score, color: '#448aff' },
          { label: '动量', value: rec.momentum_score, color: '#ff9100' },
          { label: '估值', value: rec.valuation_score, color: '#e040fb' },
          { label: '风险', value: rec.risk_score, color: '#00c853' },
        ].map((dim) => (
          <div key={dim.label} className="card metric-card">
            <div className="metric-value" style={{ color: dim.color }}>{dim.value?.toFixed(1)}/25</div>
            <div className="metric-label">{dim.label}评分</div>
          </div>
        ))}
      </div>

      <div className="rec-grid">
        <div className="card">
          <div className="card-title">看多理由</div>
          <ul className="rec-list reasons">
            {rec.reasons?.length > 0
              ? rec.reasons.map((r, i) => <li key={i}>{r}</li>)
              : <li style={{ color: '#8b8fa3' }}>暂无明确看多信号</li>}
          </ul>
        </div>
        <div className="card">
          <div className="card-title">风险提示</div>
          <ul className="rec-list risks">
            {rec.risks?.length > 0
              ? rec.risks.map((r, i) => <li key={i}>{r}</li>)
              : <li style={{ color: '#8b8fa3' }}>暂无明确风险信号</li>}
          </ul>
        </div>
      </div>

      {/* 止盈止损 */}
      {(rec.suggested_stop_loss || rec.suggested_take_profit) && (
        <div className="card" style={{ marginTop: 16 }}>
          <div className="card-title">参考价位</div>
          <div className="price-targets">
            <div className="price-target">
              <div className="label">📌 当前价</div>
              <div className="value" style={{ color: '#e1e4ed' }}>
                ¥{rec.latest_price?.toFixed(2) || '--'}
              </div>
            </div>
            {rec.suggested_stop_loss && (
              <div className="price-target">
                <div className="label">🛑 建议止损</div>
                <div className="value stop">¥{rec.suggested_stop_loss.toFixed(2)}</div>
              </div>
            )}
            {rec.suggested_take_profit && (
              <div className="price-target">
                <div className="label">🎯 建议止盈</div>
                <div className="value take">¥{rec.suggested_take_profit.toFixed(2)}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
