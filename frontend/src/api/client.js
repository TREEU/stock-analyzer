import axios from 'axios';

const API_BASE = 'http://localhost:8000/api';

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
