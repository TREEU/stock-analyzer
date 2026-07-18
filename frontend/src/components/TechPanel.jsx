import ReactECharts from 'echarts-for-react';
import { useMemo } from 'react';

function makeChartOption(data, seriesConfigs, height = 220) {
  if (!data.length) return {};
  const dates = data.map((d) => d.date);

  return {
    backgroundColor: 'transparent',
    grid: { left: 55, right: 15, top: 15, bottom: 25 },
    xAxis: {
      type: 'category', data: dates,
      axisLabel: { color: '#8b8fa3', fontSize: 10 },
      axisLine: { lineStyle: { color: '#2a2d3a' } },
    },
    yAxis: {
      type: 'value', scale: true,
      splitLine: { lineStyle: { color: '#1a1d27' } },
      axisLabel: { color: '#8b8fa3', fontSize: 10 },
    },
    series: seriesConfigs.map((s) => ({
      type: 'line', symbol: 'none',
      xAxisIndex: 0, yAxisIndex: 0,
      ...s,
    })),
    tooltip: {
      trigger: 'axis',
      backgroundColor: '#1a1d27',
      borderColor: '#2a2d3a',
      textStyle: { color: '#e1e4ed', fontSize: 11 },
    },
    legend: {
      data: seriesConfigs.map((s) => s.name),
      bottom: 0,
      textStyle: { color: '#8b8fa3', fontSize: 10 },
    },
  };
}

export default function TechPanel({ indicators }) {
  const data = indicators?.data || [];

  const macdOpt = useMemo(() => makeChartOption(data, [
    { name: 'DIF', data: data.map((d) => d.macd_dif), lineStyle: { color: '#448aff', width: 1.5 } },
    { name: 'DEA', data: data.map((d) => d.macd_dea), lineStyle: { color: '#ff9100', width: 1.5 } },
    {
      name: 'Hist', type: 'bar',
      data: data.map((d) => d.macd_hist),
      itemStyle: {
        color: (p) => p.value >= 0 ? 'rgba(0,200,83,0.5)' : 'rgba(255,61,79,0.5)',
      },
    },
  ]), [data]);

  const rsiOpt = useMemo(() => makeChartOption(data, [
    { name: 'RSI(14)', data: data.map((d) => d.rsi), lineStyle: { color: '#ffd740', width: 1.5 } },
  ]), [data]);

  const kdjOpt = useMemo(() => makeChartOption(data, [
    { name: 'K', data: data.map((d) => d.kdj_k), lineStyle: { color: '#448aff', width: 1 } },
    { name: 'D', data: data.map((d) => d.kdj_d), lineStyle: { color: '#ff9100', width: 1 } },
    { name: 'J', data: data.map((d) => d.kdj_j), lineStyle: { color: '#e040fb', width: 1 } },
  ]), [data]);

  const bollOpt = useMemo(() => {
    const close = data.map((d) => d.close);
    const upper = data.map((d) => d.boll_upper);
    const mid = data.map((d) => d.boll_mid);
    const lower = data.map((d) => d.boll_lower);
    const dates = data.map((d) => d.date);

    return {
      backgroundColor: 'transparent',
      grid: { left: 55, right: 15, top: 15, bottom: 25 },
      xAxis: {
        type: 'category', data: dates,
        axisLabel: { color: '#8b8fa3', fontSize: 10 },
        axisLine: { lineStyle: { color: '#2a2d3a' } },
      },
      yAxis: {
        type: 'value', scale: true,
        splitLine: { lineStyle: { color: '#1a1d27' } },
        axisLabel: { color: '#8b8fa3', fontSize: 10 },
      },
      series: [
        {
          name: 'K线', type: 'line', data: close,
          lineStyle: { color: '#e1e4ed', width: 1 }, symbol: 'none',
        },
        {
          name: '上轨', type: 'line', data: upper,
          lineStyle: { color: '#ff3d4f', width: 1, type: 'dashed' }, symbol: 'none',
        },
        {
          name: '中轨', type: 'line', data: mid,
          lineStyle: { color: '#8b8fa3', width: 1 }, symbol: 'none',
        },
        {
          name: '下轨', type: 'line', data: lower,
          lineStyle: { color: '#00c853', width: 1, type: 'dashed' }, symbol: 'none',
          areaStyle: { color: 'rgba(0,200,83,0.05)' },
        },
      ],
      tooltip: { trigger: 'axis', backgroundColor: '#1a1d27', borderColor: '#2a2d3a', textStyle: { color: '#e1e4ed', fontSize: 11 } },
      legend: { data: ['K线', '上轨', '中轨', '下轨'], bottom: 0, textStyle: { color: '#8b8fa3', fontSize: 10 } },
    };
  }, [data]);

  const signals = indicators?.latest_signals || {};

  return (
    <div className="panel">
      <div style={{ marginBottom: 12, display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 13 }}>
        {signals.ma_trend && <span style={{ color: signals.ma_trend.includes('多') ? '#00c853' : signals.ma_trend.includes('空') ? '#ff3d4f' : '#ffd740' }}>📊 {signals.ma_trend}</span>}
        {signals.macd_signal && <span style={{ color: signals.macd_signal.includes('金叉') || signals.macd_signal.includes('红柱') ? '#00c853' : '#ff3d4f' }}>📈 {signals.macd_signal}</span>}
        {signals.rsi_signal && <span style={{ color: signals.rsi_signal.includes('超卖') ? '#00c853' : signals.rsi_signal.includes('超买') ? '#ff3d4f' : '#8b8fa3' }}>📉 {signals.rsi_signal}</span>}
        {signals.kdj_signal && <span style={{ color: signals.kdj_signal.includes('多') ? '#00c853' : '#ff3d4f' }}>📐 {signals.kdj_signal}</span>}
        {signals.boll_signal && <span style={{ color: signals.boll_signal.includes('收窄') ? '#ffd740' : '#8b8fa3' }}>📏 {signals.boll_signal}</span>}
      </div>

      <div className="chart-grid">
        <div className="card">
          <div className="card-title">MACD</div>
          <ReactECharts option={macdOpt} style={{ height: 220 }} notMerge lazyUpdate />
        </div>
        <div className="card">
          <div className="card-title">RSI (14)</div>
          <ReactECharts option={rsiOpt} style={{ height: 220 }} notMerge lazyUpdate />
        </div>
        <div className="card">
          <div className="card-title">KDJ</div>
          <ReactECharts option={kdjOpt} style={{ height: 220 }} notMerge lazyUpdate />
        </div>
        <div className="card">
          <div className="card-title">Bollinger Bands</div>
          <ReactECharts option={bollOpt} style={{ height: 220 }} notMerge lazyUpdate />
        </div>
      </div>
    </div>
  );
}
