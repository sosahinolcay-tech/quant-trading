import { useEffect, useMemo, useState } from "react";
import { useChartStore } from "@/state/useChartStore";
import { useTabsStore } from "@/state/useTabsStore";
import { getJson } from "@/utils/api";

const STORAGE_KEY = "qt-recent-symbols";

type SearchResult = {
  symbol: string;
  name?: string;
  exchange?: string;
};

const readRecent = () => {
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as string[];
  } catch {
    return [];
  }
};

const writeRecent = (symbols: string[]) => {
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(symbols.slice(0, 10)));
  } catch {
    // ignore storage errors
  }
};

export function SearchInput() {
  const [query, setQuery] = useState("");
  const [recent, setRecent] = useState<string[]>(readRecent());
  const [open, setOpen] = useState(false);
  const [suggestions, setSuggestions] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const { setSymbol } = useChartStore();
  const { setActiveTabByView } = useTabsStore();
  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setSuggestions([]);
      setLoading(false);
      return;
    }
    setLoading(true);
    const handle = window.setTimeout(() => {
      getJson<SearchResult[]>(`/data/search?query=${encodeURIComponent(q)}`)
        .then((data) => {
          setSuggestions(data.slice(0, 5));
          setLoading(false);
        })
        .catch(() => {
          setSuggestions([]);
          setLoading(false);
        });
    }, 200);
    return () => window.clearTimeout(handle);
  }, [query]);

  const results = useMemo(() => {
    if (!suggestions.length) return [];
    return suggestions;
  }, [suggestions]);

  const applySymbol = (symbol: string) => {
    const next = [symbol, ...recent.filter((s) => s !== symbol)];
    setRecent(next);
    writeRecent(next);
    setSymbol(symbol, symbol);
    setActiveTabByView("chart");
    setQuery("");
  };

  return (
    <div className="relative">
      <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-xs text-muted">
        <span>⌘K</span>
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={(event) => {
            if (event.key === "Enter") {
              const symbol = query.trim().toUpperCase();
              if (symbol) applySymbol(symbol);
            }
          }}
          placeholder="Search markets, tickers, metrics"
          className="bg-transparent text-xs text-text placeholder:text-muted focus:outline-none"
        />
      </div>
      {open && (results.length > 0 || loading || query.trim()) && (
        <div className="absolute left-0 right-0 mt-2 rounded-xl border border-border bg-panel p-2 text-xs shadow-soft">
          {loading && <div className="px-2 py-1 text-muted">Searching...</div>}
          {results.map((item) => (
            <button
              key={item.symbol}
              type="button"
              onMouseDown={(event) => {
                event.preventDefault();
                applySymbol(item.symbol);
              }}
              className="flex w-full items-center justify-between rounded-lg px-2 py-1 text-left text-xs text-text hover:bg-white/5"
            >
              <span>{item.symbol}</span>
              <span className="text-muted">{item.name || item.exchange || "symbol"}</span>
            </button>
          ))}
          {query.trim() &&
            !results.some((item) => item.symbol === query.trim().toUpperCase()) && (
            <button
              type="button"
              onMouseDown={(event) => {
                event.preventDefault();
                applySymbol(query.trim().toUpperCase());
              }}
              className="flex w-full items-center justify-between rounded-lg px-2 py-1 text-left text-xs text-text hover:bg-white/5"
            >
              <span>Use symbol</span>
              <span className="text-muted">{query.trim().toUpperCase()}</span>
            </button>
          )}
        </div>
      )}
    </div>
  );
}
