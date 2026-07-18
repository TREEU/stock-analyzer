import axios from 'axios';

// 自动适配：
//   - 本地开发: localhost:8000
//   - 局域网手机访问: 同 IP:8000
//   - Vercel 云部署: Render 后端地址
function getApiBase() {
  const host = window.location.hostname;
  // 云部署（非本地非局域网）→ 使用 Render 后端
  if (host !== 'localhost' && host !== '127.0.0.1' && !host.startsWith('192.168.')) {
    return 'https://stock-analyzer-api.onrender.com/api';
  }
  // 本地/局域网
  return `http://${host}:8000/api`;
}

const API_BASE = getApiBase();

const client = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
});

export async function searchStocks(keyword) {
  const { data } = await client.get('/stock/search', { params: { keyword } });
  return data.results || [];
}

function today() {
  return new Date().toISOString().slice(0, 10).replace(/-/g, '');
}

export async function getFullAnalysis(code, start = '20230101', end) {
  const { data } = await client.get(`/stock/${code}/full-analysis`, {
    params: { start, end: end || today() },
  });
  return data;
}

export async function runBacktest({ code, strategy, params, start, end, initialCapital }) {
  const { data } = await client.post('/backtest', {
    code,
    strategy,
    params,
    start,
    end,
    initial_capital: initialCapital,
  });
  return data;
}

export async function getStrategies() {
  const { data } = await client.get('/backtest/strategies');
  return data.strategies || [];
}
