import { useState, useEffect, useRef } from 'react';
import { searchStocks } from '../api/client';

export default function StockSearch({ value, onChange }) {
  const [keyword, setKeyword] = useState('');
  const [results, setResults] = useState([]);
  const [open, setOpen] = useState(false);
  const [activeIdx, setActiveIdx] = useState(-1);
  const ref = useRef(null);
  const timer = useRef(null);

  useEffect(() => {
    function handleClick(e) {
      if (ref.current && !ref.current.contains(e.target)) setOpen(false);
    }
    document.addEventListener('mousedown', handleClick);
    return () => document.removeEventListener('mousedown', handleClick);
  }, []);

  const handleInput = (val) => {
    setKeyword(val);
    setActiveIdx(-1);
    if (timer.current) clearTimeout(timer.current);
    if (val.trim().length < 2) {
      setResults([]);
      setOpen(false);
      return;
    }
    timer.current = setTimeout(async () => {
      const r = await searchStocks(val);
      setResults(r);
      setOpen(r.length > 0);
    }, 300);
  };

  const select = (item) => {
    setKeyword(`${item.code} ${item.name}`);
    setOpen(false);
    onChange(item.code);
  };

  const handleKeyDown = (e) => {
    if (!open) return;
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIdx((i) => Math.min(i + 1, results.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIdx((i) => Math.max(i - 1, -1));
    } else if (e.key === 'Enter' && activeIdx >= 0) {
      select(results[activeIdx]);
    } else if (e.key === 'Escape') {
      setOpen(false);
    }
  };

  return (
    <div className="search-wrapper" ref={ref}>
      <input
        className="search-input"
        placeholder="输入股票代码或名称搜索..."
        value={keyword}
        onChange={(e) => handleInput(e.target.value)}
        onKeyDown={handleKeyDown}
        onFocus={() => results.length > 0 && setOpen(true)}
      />
      {open && (
        <div className="search-dropdown">
          {results.map((item, i) => (
            <div
              key={item.code}
              className={`search-item ${i === activeIdx ? 'active' : ''}`}
              style={i === activeIdx ? { background: 'var(--bg)' } : {}}
              onMouseEnter={() => setActiveIdx(i)}
              onClick={() => select(item)}
            >
              <span className="code">{item.code}</span>
              <span className="name">{item.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
