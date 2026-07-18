import ReactECharts from 'echarts-for-react';
import { useMemo } from 'react';

export default function PriceChart({ priceData = [], indicators = [], height = 360 }) {
  const option = useMemo(() => {
    if (!priceData.length) return {};

    const dates = priceData.map((d) => d.date);
    const ohlc = priceData.map((d) => [d.open, d.close, d.low, d.high]);
    const volumes = priceData.map((d) => d.volume);
    const mas = {};
    if (indicators.length) {
      ['ma5', 'ma10', 'ma20', 'ma60'].forEach((k) => {
        const vals = indicators.map((d) => d[k] || null);
        if (vals.some((v) => v !== null)) mas[k] = vals;
      });
    }

    return {
      backgroundColor: 'transparent',
      grid: [
        { left: 60, right: 20, top: 10, height: '55%' },
        { left: 60, right: 20, top: '72%', height: '20%' },
      ],
      xAxis: [
        { type: 'category', data: dates, gridIndex: 0, axisLabel: { show: false }, axisLine: { lineStyle: { color: '#2a2d3a' } } },
        { type: 'category', data: dates, gridIndex: 1, axisLabel: { color: '#8b8fa3', fontSize: 10 }, axisLine: { lineStyle: { color: '#2a2d3a' } } },
      ],
      yAxis: [
        { type: 'value', gridIndex: 0, scale: true, splitLine: { lineStyle: { color: '#1a1d27' } }, axisLabel: { color: '#8b8fa3', fontSize: 10 } },
        { type: 'value', gridIndex: 1, scale: true, splitLine: { lineStyle: { color: '#1a1d27' } }, axisLabel: { color: '#8b8fa3', fontSize: 10 } },
      ],
      series: [
        {
          name: 'K线', type: 'candlestick', data: ohlc,
          xAxisIndex: 0, yAxisIndex: 0,
          itemStyle: { color: '#00c853', color0: '#ff3d4f', borderColor: '#00c853', borderColor0: '#ff3d4f' },
        },
        ...Object.entries(mas).map(([key, vals]) => ({
          name: key.toUpperCase(), type: 'line', data: vals,
          xAxisIndex: 0, yAxisIndex: 0,
          symbol: 'none',
          lineStyle: { width: 1, opacity: 0.7 },
          ...(key === 'ma5' ? { lineStyle: { color: '#ffd740', width: 1 } } :
              key === 'ma10' ? { lineStyle: { color: '#448aff', width: 1 } } :
              key === 'ma20' ? { lineStyle: { color: '#ff9100', width: 1 } } :
              key === 'ma60' ? { lineStyle: { color: '#e040fb', width: 1 } } : {}),
        })),
        {
          name: '成交量', type: 'bar', data: volumes,
          xAxisIndex: 1, yAxisIndex: 1,
          itemStyle: {
            color: function (params) {
              const i = params.dataIndex;
              return ohlc[i] && ohlc[i][1] >= ohlc[i][0] ? 'rgba(0,200,83,0.4)' : 'rgba(255,61,79,0.4)';
            },
          },
        },
      ],
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'cross' },
        backgroundColor: '#1a1d27',
        borderColor: '#2a2d3a',
        textStyle: { color: '#e1e4ed', fontSize: 12 },
      },
      dataZoom: [
        { type: 'inside', xAxisIndex: [0, 1], start: 70, end: 100 },
        { type: 'slider', xAxisIndex: [0, 1], bottom: 0, height: 18, borderColor: '#2a2d3a', backgroundColor: '#1a1d27', fillerColor: 'rgba(68,138,255,0.2)' },
      ],
    };
  }, [priceData, indicators]);

  if (!priceData.length) return null;

  return (
    <div className="card">
      <ReactECharts option={option} style={{ height }} notMerge lazyUpdate />
    </div>
  );
}
