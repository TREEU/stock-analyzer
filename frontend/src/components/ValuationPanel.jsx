import ReactECharts from 'echarts-for-react';
import { useMemo } from 'react';

export default function ValuationPanel({ valuation, stockInfo }) {
  const pe = valuation?.pe_ttm;
  const pb = valuation?.pb;
  const pePct = valuation?.pe_percentile;
  const pbPct = valuation?.pb_percentile;
  const assessment = valuation?.assessment || '数据加载中...';

  const gaugeOption = (value, max, name, pct) => ({
    backgroundColor: 'transparent',
    series: [{
      type: 'gauge',
      center: ['50%', '55%'],
      radius: '85%',
      startAngle: 210, endAngle: -30,
      min: 0, max,
      splitNumber: 10,
      axisLine: {
        show: true,
        lineStyle: {
          width: 14,
          color: [
            [0.2, '#00c853'], [0.5, '#448aff'],
            [0.8, '#ff9100'], [1, '#ff3d4f'],
          ],
        },
      },
      pointer: {
        length: '60%', width: 6,
        itemStyle: { color: 'auto' },
      },
      axisTick: { distance: -12, length: 6, lineStyle: { width: 1, color: '#555' } },
      splitLine: { distance: -18, length: 14, lineStyle: { width: 2, color: '#555' } },
      axisLabel: { color: '#8b8fa3', fontSize: 10, distance: 20 },
      anchor: { show: true, showAbove: true, size: 14 },
      title: { offsetCenter: [0, '80%'], color: '#8b8fa3', fontSize: 12 },
      detail: {
        valueAnimation: true,
        fontSize: 18,
        offsetCenter: [0, '45%'],
        formatter: function (v) { return v ? v.toFixed(1) : '--'; },
        color: '#e1e4ed',
      },
      data: [{ value: value || 0, name }],
    }],
  });

  const peGauge = useMemo(() => gaugeOption(pe, 100, 'PE(TTM)', pePct), [pe, pePct]);
  const pbGauge = useMemo(() => gaugeOption(pb, 20, 'PB', pbPct), [pb, pbPct]);

  const assessmentColor =
    assessment.includes('低估') ? '#00c853' :
    assessment.includes('高估') ? '#ff3d4f' :
    assessment.includes('合理') ? '#448aff' : '#ffd740';

  return (
    <div className="panel">
      <div className="chart-grid" style={{ marginBottom: 16 }}>
        <div className="card" style={{ textAlign: 'center' }}>
          <ReactECharts option={peGauge} style={{ height: 250 }} notMerge lazyUpdate />
          {pePct != null && (
            <div style={{ fontSize: 12, color: '#8b8fa3', marginTop: -20 }}>
              PE 历史分位：{pePct.toFixed(0)}% （越低越便宜）
            </div>
          )}
        </div>
        <div className="card" style={{ textAlign: 'center' }}>
          <ReactECharts option={pbGauge} style={{ height: 250 }} notMerge lazyUpdate />
          {pbPct != null && (
            <div style={{ fontSize: 12, color: '#8b8fa3', marginTop: -20 }}>
              PB 历史分位：{pbPct.toFixed(0)}% （越低越便宜）
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <div className="card-title">估值综合评估</div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
          <div style={{
            padding: '10px 24px', borderRadius: 20,
            background: `${assessmentColor}20`, color: assessmentColor,
            fontSize: 18, fontWeight: 700,
          }}>
            {assessment}
          </div>
          <div style={{ fontSize: 13, color: '#8b8fa3' }}>
            {valuation?.index_pe != null && <div>沪深300 PE: {valuation.index_pe?.toFixed(1)}（分位 {valuation.index_pe_percentile}%）</div>}
            {valuation?.index_pb != null && <div>沪深300 PB: {valuation.index_pb?.toFixed(2)}（分位 {valuation.index_pb_percentile}%）</div>}
            {valuation?.index_pe == null && <div>PE/PB 数据来自实时行情，当前暂不可用</div>}
          </div>
        </div>
      </div>
    </div>
  );
}
