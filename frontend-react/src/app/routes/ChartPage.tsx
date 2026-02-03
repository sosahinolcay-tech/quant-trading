import { Card } from "@/components/ui/Card";
import { PriceChart } from "@/components/charts/PriceChart";
import { IndicatorLegend } from "@/components/charts/IndicatorLegend";
import { IndicatorPanels } from "@/components/charts/IndicatorPanels";
import { mockIndicators } from "@/data/mockPrices";
import { usePriceSeries } from "@/hooks/usePriceSeries";
import { macd, movingAverage, rsi } from "@/utils/indicators";

export function ChartPage() {
  const { data, loading, error } = usePriceSeries("AAPL", "1d");
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

  return (
    <div className="grid grid-cols-12 gap-4">
      <Card className="col-span-9">
        <div className="flex items-center justify-between mb-3">
          <div className="text-sm text-muted">AAPL · 1D · NASDAQ</div>
          <IndicatorLegend indicators={mockIndicators} />
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
            {mockIndicators.map((indicator) => (
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
      </Card>
    </div>
  );
}
