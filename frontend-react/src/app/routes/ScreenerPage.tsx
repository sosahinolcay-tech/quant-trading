import { useEffect, useMemo, useState } from "react";
import { ResponsiveContainer, LineChart, Line, Tooltip } from "recharts";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Tooltip as Hint } from "@/components/ui/Tooltip";
import { postJson } from "@/utils/api";
import type { PriceBar } from "@/utils/api";
import type { SeriesPoint } from "@/utils/indicators";
import { useTabsStore } from "@/state/useTabsStore";
import { useChartStore } from "@/state/useChartStore";
import { cn, formatNumber, formatPercent } from "@/utils/format";

type PairConfig = {
  id: string;
  symbolA: string;
  symbolB: string;
};

type ScreenerRow = {
  id: string;
  symbol: string;
  pair: string;
  chartSymbol: string;
  volatility: number;
  zscore: number;
  spread: number;
  corrByWindow: Record<number, number>;
  sparkline: Array<{ x: number; y: number }>;
};

const defaultPairs: PairConfig[] = [
  { id: "pair-aapl-msft", symbolA: "AAPL", symbolB: "MSFT" },
  { id: "pair-nvda-amd", symbolA: "NVDA", symbolB: "AMD" },
  { id: "pair-jpm-gs", symbolA: "JPM", symbolB: "GS" },
  { id: "pair-tsla-gm", symbolA: "TSLA", symbolB: "GM" },
  { id: "pair-xom-cvx", symbolA: "XOM", symbolB: "CVX" },
  { id: "pair-meta-googl", symbolA: "META", symbolB: "GOOGL" },
];

const PAIRS_STORAGE_KEY = "qt-screener-pairs";

const readPairs = () => {
  try {
    const raw = window.localStorage.getItem(PAIRS_STORAGE_KEY);
    if (!raw) return defaultPairs;
    const parsed = JSON.parse(raw) as PairConfig[];
    return parsed.length ? parsed : defaultPairs;
  } catch {
    return defaultPairs;
  }
};

const writePairs = (pairs: PairConfig[]) => {
  try {
    window.localStorage.setItem(PAIRS_STORAGE_KEY, JSON.stringify(pairs));
  } catch {
    // ignore storage errors
  }
};

const correlationWindows = [20, 60, 120];

const defaultRange = () => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 180);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
};

const toSeries = (rows: PriceBar[]): SeriesPoint[] =>
  rows.map((row) => ({
    timestamp: row.timestamp,
    open: row.price_open,
    high: row.price_high,
    low: row.price_low,
    close: row.price_close,
    volume: row.volume,
  }));

const alignSeries = (a: SeriesPoint[], b: SeriesPoint[]) => {
  const mapB = new Map(b.map((point) => [point.timestamp, point.close]));
  return a
    .filter((point) => mapB.has(point.timestamp))
    .map((point) => ({
      timestamp: point.timestamp,
      a: point.close,
      b: mapB.get(point.timestamp) ?? point.close,
    }));
};

const returns = (values: number[]) =>
  values.slice(1).map((value, idx) => (value - values[idx]) / values[idx]);

const std = (values: number[]) => {
  if (values.length < 2) return 0;
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
  const variance =
    values.reduce((sum, val) => sum + (val - mean) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
};

const correlation = (a: number[], b: number[]) => {
  if (a.length !== b.length || a.length < 2) return 0;
  const meanA = a.reduce((sum, val) => sum + val, 0) / a.length;
  const meanB = b.reduce((sum, val) => sum + val, 0) / b.length;
  const cov =
    a.reduce((sum, val, idx) => sum + (val - meanA) * (b[idx] - meanB), 0) / (a.length - 1);
  const denom = std(a) * std(b);
  return denom === 0 ? 0 : cov / denom;
};

const zscore = (series: number[]) => {
  if (series.length < 2) return 0;
  const mean = series.reduce((sum, val) => sum + val, 0) / series.length;
  const sigma = std(series);
  const latest = series[series.length - 1];
  return sigma === 0 ? 0 : (latest - mean) / sigma;
};

export function ScreenerPage() {
  const { setActiveTabByView } = useTabsStore();
  const { setSymbol } = useChartStore();
  const [collapsed, setCollapsed] = useState(false);
  const [volRange, setVolRange] = useState<[number, number]>([0.2, 0.6]);
  const [zThreshold, setZThreshold] = useState(1.0);
  const [spreadMax, setSpreadMax] = useState(0.35);
  const [corrWindow, setCorrWindow] = useState<number>(60);
  const [hoveredId, setHoveredId] = useState<string | null>(null);
  const [seriesMap, setSeriesMap] = useState<Record<string, SeriesPoint[]>>({});
  const [loading, setLoading] = useState(true);
  const [pairs, setPairs] = useState<PairConfig[]>(readPairs());
  const [symbolA, setSymbolA] = useState("");
  const [symbolB, setSymbolB] = useState("");

  useEffect(() => {
    let active = true;
    const { start, end } = defaultRange();
    const symbols = Array.from(new Set(pairs.flatMap((pair) => [pair.symbolA, pair.symbolB])));
    Promise.all(
      symbols.map(async (symbol) => {
        const rows = await postJson<PriceBar[]>("/data/prices", {
          symbol,
          start,
          end,
          interval: "1d",
          source: "yahoo",
        });
        return { symbol, series: toSeries(rows) };
      })
    )
      .then((data) => {
        if (!active) return;
        const next: Record<string, SeriesPoint[]> = {};
        data.forEach(({ symbol, series }) => {
          next[symbol] = series;
        });
        setSeriesMap(next);
        setLoading(false);
      })
      .catch(() => {
        if (!active) return;
        setSeriesMap({});
        setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [pairs]);

  const rows = useMemo(() => {
    if (!Object.keys(seriesMap).length) return [];
    return pairs
      .map((pair) => {
        const seriesA = seriesMap[pair.symbolA] ?? [];
        const seriesB = seriesMap[pair.symbolB] ?? [];
        const aligned = alignSeries(seriesA, seriesB);
        if (aligned.length < 40) {
          return null;
        }
        const closesA = aligned.map((item) => item.a);
        const closesB = aligned.map((item) => item.b);
        const retA = returns(closesA);
        const retB = returns(closesB);
        const spreadSeries = aligned.map(
          (item) => Math.log(item.a || 1) - Math.log(item.b || 1)
        );
        const corrByWindow: Record<number, number> = {};
        correlationWindows.forEach((window) => {
          const sliceA = retA.slice(-window);
          const sliceB = retB.slice(-window);
          corrByWindow[window] = correlation(sliceA, sliceB);
        });
        const vol = std(retA.slice(-60)) * Math.sqrt(252);
        const spreadVol = std(spreadSeries.slice(-60));
        const z = zscore(spreadSeries.slice(-60));
        const sparkline = spreadSeries.slice(-30).map((value, idx) => ({
          x: idx,
          y: value,
        }));
        return {
          id: pair.id,
          symbol: pair.symbolA,
          pair: `${pair.symbolA}/${pair.symbolB}`,
          chartSymbol: pair.symbolA,
          volatility: vol,
          zscore: z,
          spread: spreadVol,
          corrByWindow,
          sparkline,
        };
      })
      .filter(Boolean) as ScreenerRow[];
  }, [seriesMap]);

  useEffect(() => {
    if (!hoveredId && rows.length) {
      setHoveredId(rows[0].id);
    }
  }, [hoveredId, rows]);

  useEffect(() => {
    writePairs(pairs);
  }, [pairs]);

  const handleAddPair = () => {
    const a = symbolA.trim().toUpperCase();
    const b = symbolB.trim().toUpperCase();
    if (!a || !b || a === b) return;
    const id = `pair-${a}-${b}`.toLowerCase();
    if (pairs.some((pair) => pair.id === id)) return;
    setPairs((prev) => [...prev, { id, symbolA: a, symbolB: b }]);
    setSymbolA("");
    setSymbolB("");
  };

  const handleRemovePair = (id: string) => {
    setPairs((prev) => prev.filter((pair) => pair.id !== id));
  };

  const filtered = useMemo(() => {
    return rows.filter((row) => {
      const corr = row.corrByWindow[corrWindow] ?? 0;
      return (
        row.volatility >= volRange[0] &&
        row.volatility <= volRange[1] &&
        row.zscore >= zThreshold &&
        row.spread <= spreadMax &&
        corr > 0.4
      );
    });
  }, [corrWindow, rows, spreadMax, volRange, zThreshold]);

  const preview = filtered.find((row) => row.id === hoveredId) ?? filtered[0];

  return (
    <div className="flex h-full gap-4">
      <Card className={cn("transition-all", collapsed ? "w-16 p-3" : "w-64")}>
        <div className="mb-4 flex items-center justify-between">
          <div className="text-sm font-semibold">{collapsed ? "Fx" : "Filters"}</div>
          <button
            type="button"
            onClick={() => setCollapsed((prev) => !prev)}
            className="rounded-lg px-2 py-1 text-xs text-muted transition hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-accent/60"
          >
            {collapsed ? "›" : "‹"}
          </button>
        </div>
        {!collapsed && (
          <div className="space-y-5 text-sm">
            <div>
              <Hint label="Choose the symbol pair universe">
                <div className="mb-2 text-xs uppercase text-muted">Universe</div>
              </Hint>
              <div className="flex items-center gap-2">
                <input
                  value={symbolA}
                  onChange={(event) => setSymbolA(event.target.value.toUpperCase())}
                  placeholder="Symbol A"
                  className="w-1/2 rounded-lg border border-border bg-panel px-2 py-1.5 text-xs text-text focus-visible:ring-2 focus-visible:ring-accent/60"
                />
                <input
                  value={symbolB}
                  onChange={(event) => setSymbolB(event.target.value.toUpperCase())}
                  placeholder="Symbol B"
                  className="w-1/2 rounded-lg border border-border bg-panel px-2 py-1.5 text-xs text-text focus-visible:ring-2 focus-visible:ring-accent/60"
                />
              </div>
              <button
                type="button"
                onClick={handleAddPair}
                className="mt-2 rounded-lg border border-border px-2 py-1 text-xs text-text hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-accent/60"
              >
                Add pair
              </button>
              <div className="mt-2 flex flex-wrap gap-2 text-xs">
                {pairs.map((pair) => (
                  <button
                    key={pair.id}
                    type="button"
                    onClick={() => handleRemovePair(pair.id)}
                    className="rounded-lg border border-border bg-panel/60 px-2 py-1 text-xs text-text hover:border-accent/60"
                  >
                    {pair.symbolA}/{pair.symbolB}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <Hint label="Annualized realized volatility">
                <div className="mb-2 text-xs uppercase text-muted">Volatility</div>
              </Hint>
              <div className="flex items-center gap-2 text-xs text-muted">
                <span>{formatPercent(volRange[0] * 100)}</span>
                <span>—</span>
                <span>{formatPercent(volRange[1] * 100)}</span>
              </div>
              <input
                type="range"
                min={0.1}
                max={0.8}
                step={0.01}
                value={volRange[0]}
                onChange={(event) => {
                  const next = Math.min(Number(event.target.value), volRange[1] - 0.01);
                  setVolRange([next, volRange[1]]);
                }}
                className="mt-2 w-full accent-accent focus-visible:ring-2 focus-visible:ring-accent/60"
              />
              <input
                type="range"
                min={0.1}
                max={0.8}
                step={0.01}
                value={volRange[1]}
                onChange={(event) => {
                  const next = Math.max(Number(event.target.value), volRange[0] + 0.01);
                  setVolRange([volRange[0], next]);
                }}
                className="mt-2 w-full accent-accent focus-visible:ring-2 focus-visible:ring-accent/60"
              />
            </div>

            <div>
              <Hint label="Correlation lookback window">
                <div className="mb-2 text-xs uppercase text-muted">Rolling correlation</div>
              </Hint>
              <select
                value={corrWindow}
                onChange={(event) => setCorrWindow(Number(event.target.value))}
                className="w-full rounded-lg border border-border bg-panel px-3 py-2 text-xs text-text focus-visible:ring-2 focus-visible:ring-accent/60"
              >
                {correlationWindows.map((window) => (
                  <option key={window} value={window}>
                    {window} sessions
                  </option>
                ))}
              </select>
            </div>

            <div>
              <Hint label="Minimum standardized deviation">
                <div className="mb-2 text-xs uppercase text-muted">Z-score threshold</div>
              </Hint>
              <div className="flex items-center justify-between text-xs text-muted">
                <span>{formatNumber(zThreshold)}</span>
                <span>3.0</span>
              </div>
              <input
                type="range"
                min={0.5}
                max={3}
                step={0.1}
                value={zThreshold}
                onChange={(event) => setZThreshold(Number(event.target.value))}
                className="mt-2 w-full accent-accent focus-visible:ring-2 focus-visible:ring-accent/60"
              />
            </div>

            <div>
              <Hint label="Bid/ask spread proxy">
                <div className="mb-2 text-xs uppercase text-muted">Spread / liquidity</div>
              </Hint>
              <div className="flex items-center justify-between text-xs text-muted">
                <span>{formatNumber(spreadMax)}</span>
                <span>0.40</span>
              </div>
              <input
                type="range"
                min={0.04}
                max={0.4}
                step={0.01}
                value={spreadMax}
                onChange={(event) => setSpreadMax(Number(event.target.value))}
                className="mt-2 w-full accent-accent focus-visible:ring-2 focus-visible:ring-accent/60"
              />
            </div>
          </div>
        )}
      </Card>

      <Card className="flex-1 overflow-hidden">
        <div className="mb-3 flex items-center justify-between">
          <div>
            <div className="text-sm font-semibold">Discovery Results</div>
            <div className="text-xs text-muted">
              {filtered.length} candidates • corr {corrWindow}d
            </div>
          </div>
          <div className="text-xs text-muted">Hover to preview, click to chart</div>
        </div>
        <div className="overflow-auto rounded-lg border border-border">
          <table className="w-full text-left text-xs">
            <thead className="bg-panel text-muted">
              <tr>
                <th className="px-3 py-2">Symbol / Pair</th>
                <th className="px-3 py-2">Volatility</th>
                <th className="px-3 py-2">Correlation</th>
                <th className="px-3 py-2">Z-score</th>
                <th className="px-3 py-2">Spread</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                Array.from({ length: 6 }).map((_, idx) => (
                  <tr key={`loading-${idx}`} className="border-t border-border">
                    <td className="px-3 py-2">
                      <Skeleton className="h-4 w-24" />
                      <Skeleton className="mt-1 h-3 w-16" />
                    </td>
                    <td className="px-3 py-2">
                      <Skeleton className="h-4 w-14" />
                    </td>
                    <td className="px-3 py-2">
                      <Skeleton className="h-4 w-14" />
                    </td>
                    <td className="px-3 py-2">
                      <Skeleton className="h-4 w-14" />
                    </td>
                    <td className="px-3 py-2">
                      <Skeleton className="h-4 w-14" />
                    </td>
                  </tr>
                ))
              ) : (
                filtered.map((row) => {
                const corr = row.corrByWindow[corrWindow] ?? 0;
                const active = row.id === preview?.id;
                return (
                  <tr
                    key={row.id}
                    tabIndex={0}
                    onMouseEnter={() => setHoveredId(row.id)}
                    onFocus={() => setHoveredId(row.id)}
                    onClick={() => {
                      setSymbol(row.chartSymbol, row.pair);
                      setActiveTabByView("chart");
                    }}
                    className={cn(
                      "cursor-pointer border-t border-border text-text transition hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-accent/50",
                      active && "bg-white/5"
                    )}
                  >
                    <td className="px-3 py-2">
                      <div className="text-sm font-semibold">{row.symbol}</div>
                      <div className="text-[11px] text-muted">{row.pair}</div>
                    </td>
                    <td className="px-3 py-2">{formatPercent(row.volatility * 100)}</td>
                    <td className="px-3 py-2">{formatNumber(corr)}</td>
                    <td className="px-3 py-2">{formatNumber(row.zscore)}</td>
                    <td className="px-3 py-2">{formatNumber(row.spread)}</td>
                  </tr>
                );
              })
              )}
              {!loading && !filtered.length && (
                <tr>
                  <td colSpan={5} className="px-3 py-6 text-center text-xs text-muted">
                    No matches for the current filters.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </Card>

      <Card className="w-72">
        <div className="mb-3 text-sm font-semibold">Context Preview</div>
        {!preview ? (
          <div className="space-y-3">
            <Skeleton className="h-24 w-full" />
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-10 w-full" />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="rounded-lg border border-border bg-panel/60 p-3">
              <div className="text-xs text-muted">{preview.pair}</div>
              <div className="text-lg font-semibold">{preview.symbol}</div>
              <div className="mt-2 h-24">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={preview.sparkline}>
                    <Tooltip
                      cursor={{ stroke: "rgba(255,255,255,0.2)" }}
                      contentStyle={{
                        background: "#0F1424",
                        border: "1px solid rgba(255,255,255,0.08)",
                      }}
                    />
                    <Line
                      type="monotone"
                      dataKey="y"
                      stroke="#7C5CFF"
                      strokeWidth={2}
                      dot={false}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3 text-xs">
              <div className="rounded-lg border border-border bg-panel/60 p-3">
                <div className="text-muted">Volatility</div>
                <div className="text-sm font-semibold">
                  {formatPercent(preview.volatility * 100)}
                </div>
              </div>
              <div className="rounded-lg border border-border bg-panel/60 p-3">
                <div className="text-muted">Z-score</div>
                <div className="text-sm font-semibold">{formatNumber(preview.zscore)}</div>
              </div>
              <div className="rounded-lg border border-border bg-panel/60 p-3">
                <div className="text-muted">Correlation</div>
                <div className="text-sm font-semibold">
                  {formatNumber(preview.corrByWindow[corrWindow] ?? 0)}
                </div>
              </div>
              <div className="rounded-lg border border-border bg-panel/60 p-3">
                <div className="text-muted">Spread</div>
                <div className="text-sm font-semibold">{formatNumber(preview.spread)}</div>
              </div>
            </div>
            <div className="text-xs text-muted">
              Preview updates on hover. Click a row to open the chart workspace.
            </div>
          </div>
        )}
      </Card>
    </div>
  );
}
