import { useEffect, useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { useNews } from "@/hooks/useNews";
import { postJson } from "@/utils/api";
import type { PriceBar } from "@/utils/api";
import type { SeriesPoint } from "@/utils/indicators";
import { movingAverage } from "@/utils/indicators";
import { cn, formatCurrency, formatNumber, formatPercent, formatTimestamp } from "@/utils/format";

type PositionRow = {
  symbol: string;
  qty: number;
  avgPrice: number;
  lastPrice: number;
  pnl: number;
};

type TradeRow = {
  id: string;
  symbol: string;
  side: "BUY" | "SELL";
  qty: number;
  price: number;
  timestamp: string;
};

const portfolioSymbols = ["AAPL", "MSFT", "NVDA", "JPM", "XOM"];

const defaultRange = () => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 120);
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

type SortKey = keyof PositionRow;

export function PortfolioPage() {
  const [hoveredSymbol, setHoveredSymbol] = useState<string | null>(portfolioSymbols[0] ?? null);
  const [sortKey, setSortKey] = useState<SortKey>("pnl");
  const [sortDir, setSortDir] = useState<"asc" | "desc">("desc");
  const [seriesMap, setSeriesMap] = useState<Record<string, SeriesPoint[]>>({});
  const [loading, setLoading] = useState(true);
  const { items: newsItems, loading: newsLoading } = useNews();

  useEffect(() => {
    let active = true;
    const { start, end } = defaultRange();
    Promise.all(
      portfolioSymbols.map(async (symbol) => {
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
  }, []);

  const positions = useMemo(() => {
    const notional = 25000;
    return portfolioSymbols
      .map((symbol) => {
        const series = seriesMap[symbol] ?? [];
        if (series.length < 5) return null;
        const last = series[series.length - 1];
        const recent = series.slice(-20);
        const avg =
          recent.reduce((sum, point) => sum + point.close, 0) / Math.max(recent.length, 1);
        const qty = Math.max(1, Math.round(notional / last.close));
        const pnl = (last.close - avg) * qty;
        return {
          symbol,
          qty,
          avgPrice: avg,
          lastPrice: last.close,
          pnl,
        };
      })
      .filter(Boolean) as PositionRow[];
  }, [seriesMap]);

  const sortedPositions = useMemo(() => {
    return [...positions].sort((a, b) => {
      const dir = sortDir === "asc" ? 1 : -1;
      if (a[sortKey] < b[sortKey]) return -1 * dir;
      if (a[sortKey] > b[sortKey]) return 1 * dir;
      return 0;
    });
  }, [positions, sortDir, sortKey]);

  const inventory = useMemo(() => {
    const symbol = hoveredSymbol ?? portfolioSymbols[0];
    const series = seriesMap[symbol] ?? [];
    if (!series.length) return [];
    const ma20 = movingAverage(series, 20);
    const qty = positions.find((row) => row.symbol === symbol)?.qty ?? 0;
    return series.slice(-30).map((point, idx) => {
      const ma = ma20[series.length - 30 + idx];
      const pos = ma && point.close > ma ? qty : 0;
      return { x: point.timestamp, y: pos };
    });
  }, [hoveredSymbol, positions, seriesMap]);

  const portfolioSeries = useMemo(() => {
    if (!portfolioSymbols.every((symbol) => seriesMap[symbol]?.length)) return [];
    const firstSymbol = portfolioSymbols[0];
    const timestamps = seriesMap[firstSymbol].map((point) => point.timestamp);
    const notional = 25000;
    const basePrices = portfolioSymbols.reduce<Record<string, number>>((acc, symbol) => {
      acc[symbol] = seriesMap[symbol][0]?.close ?? 1;
      return acc;
    }, {});
    return timestamps
      .map((timestamp) => {
        let value = 0;
        for (const symbol of portfolioSymbols) {
          const series = seriesMap[symbol];
          const point = series.find((p) => p.timestamp === timestamp);
          if (!point) return null;
          const qty = notional / (basePrices[symbol] || 1);
          value += qty * point.close;
        }
        return { x: timestamp, y: value };
      })
      .filter(Boolean) as Array<{ x: number; y: number }>;
  }, [seriesMap]);

  const pnlSeries = useMemo(() => {
    if (!portfolioSeries.length) return [];
    const base = portfolioSeries[0].y;
    return portfolioSeries.map((point) => ({ x: point.x, y: point.y - base }));
  }, [portfolioSeries]);

  const drawdownSeries = useMemo(() => {
    let peak = -Infinity;
    return pnlSeries.map((point) => {
      peak = Math.max(peak, point.y);
      return { x: point.x, y: Math.min(0, point.y - peak) };
    });
  }, [pnlSeries]);

  const trades = useMemo(() => {
    const entries: TradeRow[] = [];
    portfolioSymbols.forEach((symbol) => {
      const series = seriesMap[symbol] ?? [];
      if (series.length < 25) return;
      const ma20 = movingAverage(series, 20);
      let inPosition = false;
      for (let i = 21; i < series.length; i += 1) {
        const ma = ma20[i];
        if (!ma) continue;
        const price = series[i].close;
        if (!inPosition && price > ma) {
          inPosition = true;
          entries.push({
            id: `${symbol}-buy-${series[i].timestamp}`,
            symbol,
            side: "BUY",
            qty: Math.round(25000 / price),
            price,
            timestamp: formatTimestamp(series[i].timestamp),
          });
        } else if (inPosition && price < ma) {
          inPosition = false;
          entries.push({
            id: `${symbol}-sell-${series[i].timestamp}`,
            symbol,
            side: "SELL",
            qty: Math.round(25000 / price),
            price,
            timestamp: formatTimestamp(series[i].timestamp),
          });
        }
      }
    });
    return entries.slice(-12).reverse();
  }, [seriesMap]);

  const exposure = positions.reduce((sum, row) => sum + Math.abs(row.qty * row.lastPrice), 0);
  const totalPnl = pnlSeries[pnlSeries.length - 1]?.y ?? 0;
  const sharpe = useMemo(() => {
    if (pnlSeries.length < 2) return 0;
    const returns = pnlSeries.slice(1).map((point, idx) => point.y - pnlSeries[idx].y);
    const mean = returns.reduce((sum, val) => sum + val, 0) / returns.length;
    const variance =
      returns.reduce((sum, val) => sum + (val - mean) ** 2, 0) / Math.max(returns.length - 1, 1);
    const sigma = Math.sqrt(variance);
    return sigma === 0 ? 0 : (mean / sigma) * Math.sqrt(252);
  }, [pnlSeries]);
  const maxDrawdown = Math.min(...drawdownSeries.map((point) => point.y), 0);

  const toggleSort = (key: SortKey) => {
    if (key === sortKey) {
      setSortDir((prev) => (prev === "asc" ? "desc" : "asc"));
      return;
    }
    setSortKey(key);
    setSortDir("desc");
  };

  return (
    <div className="flex h-full flex-col gap-4 pb-4">
      <div className="grid grid-cols-4 gap-3">
        {[
          { label: "Total PnL", value: formatCurrency(totalPnl) },
          { label: "Sharpe", value: sharpe.toFixed(2) },
          { label: "Max drawdown", value: formatPercent(maxDrawdown * 100) },
          { label: "Exposure", value: formatCurrency(exposure) },
        ].map((metric) => (
          <Card key={metric.label} className="p-3">
            <div className="text-xs text-muted">{metric.label}</div>
            <div className="text-sm font-semibold">{metric.value}</div>
          </Card>
        ))}
      </div>

      <div className="grid grid-cols-2 gap-4">
        <Card className="flex flex-col gap-4">
          <div className="text-sm font-semibold">Positions</div>
          <div className="overflow-auto rounded-lg border border-border">
            <table className="w-full text-left text-xs">
              <thead className="bg-panel text-muted">
                <tr>
                  <th className="px-3 py-2">Symbol</th>
                  <th className="px-3 py-2 cursor-pointer" onClick={() => toggleSort("qty")}>
                    Qty
                  </th>
                  <th className="px-3 py-2 cursor-pointer" onClick={() => toggleSort("avgPrice")}>
                    Avg Px
                  </th>
                  <th className="px-3 py-2 cursor-pointer" onClick={() => toggleSort("lastPrice")}>
                    Last Px
                  </th>
                  <th className="px-3 py-2 cursor-pointer" onClick={() => toggleSort("pnl")}>
                    PnL
                  </th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={5} className="px-3 py-4 text-center text-xs text-muted">
                      Loading positions...
                    </td>
                  </tr>
                ) : (
                  sortedPositions.map((row) => (
                  <tr
                    key={row.symbol}
                    tabIndex={0}
                    onMouseEnter={() => setHoveredSymbol(row.symbol)}
                    onFocus={() => setHoveredSymbol(row.symbol)}
                    className={cn(
                      "border-t border-border text-text transition hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-accent/50",
                      hoveredSymbol === row.symbol && "bg-white/5"
                    )}
                  >
                    <td className="px-3 py-2 text-sm font-semibold">{row.symbol}</td>
                    <td className="px-3 py-2">{formatNumber(row.qty)}</td>
                    <td className="px-3 py-2">{formatCurrency(row.avgPrice)}</td>
                    <td className="px-3 py-2">{formatCurrency(row.lastPrice)}</td>
                    <td
                      className={cn(
                        "px-3 py-2",
                        row.pnl >= 0 ? "text-emerald-300" : "text-rose-300"
                      )}
                    >
                      {formatCurrency(row.pnl)}
                    </td>
                  </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="rounded-xl border border-border bg-panel/60 p-3">
            <div className="text-xs text-muted">
              Inventory over time · {hoveredSymbol ?? "AAPL"}
            </div>
            <div className="mt-2 h-40">
              {loading ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={inventory}>
                    <XAxis dataKey="x" hide />
                    <YAxis hide />
                    <Tooltip
                      cursor={{ stroke: "rgba(255,255,255,0.1)" }}
                      contentStyle={{
                        background: "#0F1424",
                        border: "1px solid rgba(255,255,255,0.08)",
                      }}
                    />
                    <Line type="monotone" dataKey="y" stroke="#38BDF8" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
        </Card>

        <Card className="flex flex-col gap-4">
          <div className="text-sm font-semibold">Performance</div>
          <div className="rounded-xl border border-border bg-panel/60 p-3">
            <div className="text-xs text-muted">PnL curve</div>
            <div className="mt-2 h-40">
              {loading ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={pnlSeries}>
                    <XAxis dataKey="x" hide />
                    <YAxis hide />
                    <Tooltip
                      cursor={{ stroke: "rgba(255,255,255,0.1)" }}
                      contentStyle={{
                        background: "#0F1424",
                        border: "1px solid rgba(255,255,255,0.08)",
                      }}
                    />
                    <Line type="monotone" dataKey="y" stroke="#7C5CFF" dot={false} />
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
          <div className="rounded-xl border border-border bg-panel/60 p-3">
            <div className="text-xs text-muted">Drawdown curve</div>
            <div className="mt-2 h-40">
              {loading ? (
                <Skeleton className="h-full w-full" />
              ) : (
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={drawdownSeries}>
                    <XAxis dataKey="x" hide />
                    <YAxis hide />
                    <Tooltip
                      cursor={{ stroke: "rgba(255,255,255,0.1)" }}
                      contentStyle={{
                        background: "#0F1424",
                        border: "1px solid rgba(255,255,255,0.08)",
                      }}
                    />
                    <Area type="monotone" dataKey="y" stroke="#FF6B6B" fill="#FF6B6B33" />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </div>
          <div className="rounded-xl border border-border bg-panel/60 p-3">
            <div className="text-xs text-muted">News feed</div>
            <div className="mt-2 max-h-40 space-y-2 overflow-auto text-xs">
              {newsLoading ? (
                <>
                  <Skeleton className="h-4 w-full" />
                  <Skeleton className="h-4 w-4/5" />
                  <Skeleton className="h-4 w-3/5" />
                </>
              ) : newsItems.length === 0 ? (
                <div className="text-xs text-muted">No news available.</div>
              ) : (
                newsItems.map((item) => (
                  <div key={item.id} className="border-b border-border/60 pb-2">
                    <div className="text-sm leading-snug text-text">{item.headline}</div>
                    <div className="text-[11px] text-muted">
                      {item.source} · {item.time}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>
        </Card>
      </div>

      <Card>
        <div className="mb-2 text-sm font-semibold">Trade log</div>
        <div className="max-h-56 overflow-y-auto rounded-lg border border-border bg-panel/60">
          <table className="w-full text-left text-xs">
            <thead className="sticky top-0 bg-panel text-muted">
              <tr>
                <th className="px-3 py-2">Time</th>
                <th className="px-3 py-2">Symbol</th>
                <th className="px-3 py-2">Side</th>
                <th className="px-3 py-2">Qty</th>
                <th className="px-3 py-2">Price</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan={5} className="px-3 py-4 text-center text-xs text-muted">
                    Loading trades...
                  </td>
                </tr>
              ) : (
                trades.map((row, idx) => (
                <tr
                  key={row.id}
                  className={cn(
                    "border-t border-border text-text",
                    idx % 2 === 0 ? "bg-white/2" : "bg-transparent"
                  )}
                >
                  <td className="px-3 py-1.5">{row.timestamp}</td>
                  <td className="px-3 py-1.5">{row.symbol}</td>
                  <td
                    className={cn(
                      "px-3 py-1.5 font-semibold",
                      row.side === "BUY" ? "text-emerald-300" : "text-rose-300"
                    )}
                  >
                    {row.side}
                  </td>
                  <td className="px-3 py-1.5">{formatNumber(row.qty)}</td>
                  <td className="px-3 py-1.5">{formatCurrency(row.price)}</td>
                </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </Card>
    </div>
  );
}
