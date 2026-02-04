import { useEffect, useMemo, useState } from "react";
import { Card } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { PriceChart } from "@/components/charts/PriceChart";
import { IndicatorLegend } from "@/components/charts/IndicatorLegend";
import { IndicatorPanels } from "@/components/charts/IndicatorPanels";
import { usePriceSeries } from "@/hooks/usePriceSeries";
import { useChartStore } from "@/state/useChartStore";
import { macd, movingAverage, rsi } from "@/utils/indicators";
import { getJson } from "@/utils/api";

const indicatorLabels = ["MA 20", "MA 50", "RSI", "MACD"];

export function ChartPage() {
  const { symbol, display, setSymbol } = useChartStore();
  const [input, setInput] = useState(symbol);
  const [news, setNews] = useState<Array<{ id: string; headline: string; source: string; time: string }>>(
    []
  );
  const [newsLoading, setNewsLoading] = useState(true);
  const { data, loading, error } = usePriceSeries(symbol, "1d");
  const ma20 = movingAverage(data, 20);
  const ma50 = movingAverage(data, 50);
  const rsiSeries = rsi(data);
  const macdSeries = macd(data);
  const chartData = data.map((point, idx) => ({
    ...point,
    ma20: ma20[idx],
    ma50: ma50[idx],
    rsi: rsiSeries[idx],
    macd: macdSeries.macd[idx],
    signal: macdSeries.signal[idx],
  }));

  useEffect(() => {
    setNewsLoading(true);
    getJson<Array<{ id: string; headline: string; source: string; time: string }>>(
      `/data/news?symbol=${encodeURIComponent(symbol)}`
    )
      .then((items) => {
        setNews(items.slice(0, 6));
        setNewsLoading(false);
      })
      .catch(() => {
        setNews([]);
        setNewsLoading(false);
      });
  }, [symbol]);

  const insight = useMemo(() => {
    if (!news.length) return null;
    const positive = ["beats", "surge", "rally", "upgrade", "raises", "record", "growth"];
    const negative = ["miss", "downgrade", "cuts", "falls", "slump", "probe", "lawsuit"];
    let score = 0;
    const themes: Record<string, number> = {};
    news.forEach((item) => {
      const text = item.headline.toLowerCase();
      positive.forEach((word) => {
        if (text.includes(word)) score += 1;
      });
      negative.forEach((word) => {
        if (text.includes(word)) score -= 1;
      });
      if (text.includes("earnings")) themes.earnings = (themes.earnings || 0) + 1;
      if (text.includes("guidance")) themes.guidance = (themes.guidance || 0) + 1;
      if (text.includes("ai")) themes.ai = (themes.ai || 0) + 1;
      if (text.includes("regulator") || text.includes("probe")) themes.regulation = (themes.regulation || 0) + 1;
    });
    const bias = score > 1 ? "Bullish" : score < -1 ? "Bearish" : "Neutral";
    const topTheme = Object.entries(themes).sort((a, b) => b[1] - a[1])[0]?.[0];
    return { bias, score, topTheme };
  }, [news]);

  return (
    <div className="grid grid-cols-12 gap-4">
      <Card className="col-span-9">
        <div className="flex flex-wrap items-center justify-between gap-3 mb-3">
          <div className="text-sm text-muted">{display} · 1D · NASDAQ</div>
          <div className="flex items-center gap-2">
            <input
              value={input}
              onChange={(event) => setInput(event.target.value.toUpperCase())}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  const next = input.trim().toUpperCase();
                  if (next) {
                    setSymbol(next, next);
                  }
                }
              }}
              placeholder="Symbol"
              className="h-8 w-24 rounded-lg border border-border bg-panel px-2 text-xs text-text focus-visible:ring-2 focus-visible:ring-accent/60"
            />
            <Button
              variant="ghost"
              className="h-8 px-2 text-xs"
              onClick={() => {
                const next = input.trim().toUpperCase();
                if (next) {
                  setSymbol(next, next);
                }
              }}
            >
              Load
            </Button>
            <IndicatorLegend indicators={indicatorLabels} />
          </div>
        </div>
        {loading && <div className="text-sm text-muted">Loading price data...</div>}
        {error && <div className="text-sm text-red-400">{error}</div>}
        {!loading && !error && <PriceChart data={chartData} />}
        {!loading && !error && <IndicatorPanels data={chartData} />}
      </Card>
      <Card className="col-span-3 space-y-4">
        <div>
          <div className="text-xs uppercase tracking-wide text-muted">Indicators</div>
          <div className="mt-3 space-y-2 text-sm">
            {indicatorLabels.map((indicator) => (
              <div key={indicator} className="flex items-center justify-between">
                <span>{indicator}</span>
                <span className="text-muted">active</span>
              </div>
            ))}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-muted">Order Flow</div>
          <div className="mt-3 space-y-2 text-sm">
            {chartData.slice(-4).map((point, idx) => {
              const side = point.close >= (chartData[idx - 1]?.close ?? point.close) ? "BUY" : "SELL";
              return (
                <div key={point.timestamp} className="flex items-center justify-between">
                  <span>{side} · {Math.round(point.volume)}</span>
                  <span className={side === "BUY" ? "text-emerald-400" : "text-red-400"}>
                    {point.close.toFixed(2)}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
        <div>
          <div className="text-xs uppercase tracking-wide text-muted">AI News Insight</div>
          <div className="mt-3 space-y-2 text-xs">
            {newsLoading ? (
              <div className="text-muted">Loading news...</div>
            ) : news.length === 0 ? (
              <div className="text-muted">No news available.</div>
            ) : (
              <>
                <div className="rounded-lg border border-border bg-panel/60 px-2 py-2 text-xs">
                  <div className="text-muted">Bias</div>
                  <div className="text-sm font-semibold">{insight?.bias ?? "Neutral"}</div>
                  <div className="text-muted">Mentions: {news.length}</div>
                  {insight?.topTheme && (
                    <div className="text-muted">Theme: {insight.topTheme}</div>
                  )}
                </div>
                <div className="space-y-2">
                  {news.map((item) => (
                    <div key={item.id} className="border-b border-border/60 pb-2">
                      <div className="text-sm leading-snug">{item.headline}</div>
                      <div className="text-[11px] text-muted">
                        {item.source} · {item.time}
                      </div>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        </div>
      </Card>
    </div>
  );
}
