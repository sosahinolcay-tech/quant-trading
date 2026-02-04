import { useState } from "react";
import { PriceChart } from "@/components/charts/PriceChart";
import { usePriceSeries } from "@/hooks/usePriceSeries";
import { movingAverage } from "@/utils/indicators";

type OhlcChartWidgetProps = {
  symbol: string;
  onSymbolChange?: (symbol: string) => void;
};

export function OhlcChartWidget({ symbol, onSymbolChange }: OhlcChartWidgetProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(symbol);
  const { data, loading, error } = usePriceSeries(symbol, "1d");
  const ma20 = movingAverage(data, 20);
  const ma50 = movingAverage(data, 50);
  const chartData = data.map((point, idx) => ({
    ...point,
    ma20: ma20[idx],
    ma50: ma50[idx],
  }));
  const last = data[data.length - 1];
  const prev = data[data.length - 2] ?? last;
  const changePct =
    last && prev && prev.close ? ((last.close - prev.close) / prev.close) * 100 : 0;

  return (
    <div className="h-full p-2">
      <div className="widget-handle mb-1.5 flex items-center justify-between gap-2">
        <div className="text-xs font-semibold">{symbol} · OHLC</div>
        <div className="flex items-center gap-2">
          {editing ? (
            <>
              <input
                value={draft}
                onChange={(event) => setDraft(event.target.value.toUpperCase())}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    const next = draft.trim().toUpperCase();
                    if (next) onSymbolChange?.(next);
                    setEditing(false);
                  }
                }}
                className="h-6 w-20 rounded-lg border border-border bg-panel px-2 text-[10px] text-text focus-visible:ring-2 focus-visible:ring-accent/60"
              />
              <button
                type="button"
                onClick={() => {
                  const next = draft.trim().toUpperCase();
                  if (next) onSymbolChange?.(next);
                  setEditing(false);
                }}
                className="text-[10px] text-muted hover:text-text"
              >
                Apply
              </button>
            </>
          ) : (
            <button
              type="button"
              onClick={() => {
                setDraft(symbol);
                setEditing(true);
              }}
              className="text-[10px] text-muted hover:text-text"
            >
              Edit
            </button>
          )}
          <span className="text-[10px] text-muted">1D · NYSE</span>
        </div>
      </div>
      {last && !loading && !error && (
        <div className="mb-1 text-[11px] text-muted">
          Last {last.close.toFixed(2)} · {changePct >= 0 ? "+" : ""}
          {changePct.toFixed(2)}%
        </div>
      )}
      {loading && <div className="text-xs text-muted">Loading chart...</div>}
      {error && <div className="text-xs text-red-400">{error}</div>}
      {!loading && !error && <PriceChart height={180} data={chartData} />}
    </div>
  );
}
