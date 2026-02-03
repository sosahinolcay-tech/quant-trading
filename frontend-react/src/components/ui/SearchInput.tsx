import { useMemo, useState } from "react";

const searchPool = [
  { symbol: "AAPL", name: "Apple" },
  { symbol: "MSFT", name: "Microsoft" },
  { symbol: "NVDA", name: "NVIDIA" },
  { symbol: "AMZN", name: "Amazon" },
  { symbol: "SPY", name: "S&P 500 ETF" },
  { symbol: "QQQ", name: "Nasdaq 100 ETF" },
];

export function SearchInput() {
  const [query, setQuery] = useState("");
  const results = useMemo(() => {
    const q = query.toLowerCase();
    if (!q) return [];
    return searchPool.filter((item) => item.symbol.toLowerCase().includes(q) || item.name.toLowerCase().includes(q));
  }, [query]);

  return (
    <div className="relative">
      <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-xs text-muted">
        <span>⌘K</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search markets, tickers, metrics"
          className="bg-transparent text-xs text-text placeholder:text-muted focus:outline-none"
        />
      </div>
      {results.length > 0 && (
        <div className="absolute left-0 right-0 mt-2 rounded-xl border border-border bg-panel p-2 text-xs shadow-soft">
          {results.slice(0, 5).map((item) => (
            <div key={`${item.symbol}-${item.name}`} className="flex justify-between py-1">
              <span>{item.symbol}</span>
              <span className="text-muted">{item.name}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
