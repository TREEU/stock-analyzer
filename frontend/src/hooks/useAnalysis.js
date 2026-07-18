import { useState, useEffect, useCallback } from 'react';
import { getFullAnalysis, runBacktest, getStrategies } from '../api/client';

export function useAnalysis() {
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [data, setData] = useState(null);
  const [backtestResult, setBacktestResult] = useState(null);
  const [backtestLoading, setBacktestLoading] = useState(false);
  const [strategies, setStrategies] = useState([]);

  // 加载可用策略列表
  useEffect(() => {
    getStrategies().then(setStrategies).catch(() => {});
  }, []);

  // 当 code 改变时加载全量分析
  useEffect(() => {
    if (!code) {
      setData(null);
      setError(null);
      return;
    }

    let cancelled = false;
    setLoading(true);
    setError(null);
    setBacktestResult(null);

    getFullAnalysis(code)
      .then((res) => {
        if (!cancelled) {
          setData(res);
          setLoading(false);
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.response?.data?.detail || err.message || '数据加载失败');
          setLoading(false);
        }
      });

    return () => { cancelled = true; };
  }, [code]);

  // 回测
  const executeBacktest = useCallback(async (backtestParams) => {
    setBacktestLoading(true);
    try {
      const result = await runBacktest({
        code,
        ...backtestParams,
      });
      setBacktestResult(result);
      return result;
    } catch (err) {
      throw err;
    } finally {
      setBacktestLoading(false);
    }
  }, [code]);

  return {
    code,
    setCode,
    loading,
    error,
    data,
    backtestResult,
    backtestLoading,
    executeBacktest,
    strategies,
  };
}
