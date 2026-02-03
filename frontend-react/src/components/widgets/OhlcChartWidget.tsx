import { PriceChart } from "@/components/charts/PriceChart";
import { usePriceSeries } from "@/hooks/usePriceSeries";
import { movingAverage } from "@/utils/indicators";

export function OhlcChartWidget() {
  const { data, loading, error } = usePriceSeries("AAPL", "1d");
  const ma20 = movingAverage(data, 20);
  const ma50 = movingAverage(data, 50);
  const chartData = data.map((point, idx) => ({
    ...point,
    ma20: ma20[idx],
    ma50: ma50[idx],
  }));

  return (
    <div className="h-full p-4">
      <div className="widget-handle mb-3 flex items-center justify-between">
        <div className="text-sm font-semibold">AAPL · OHLC</div>
        <span className="text-xs text-muted">1D · NYSE</span>
      </div>
      {loading && <div className="text-sm text-muted">Loading chart...</div>}
      {error && <div className="text-sm text-red-400">{error}</div>}
      {!loading && !error && <PriceChart height={280} data={chartData} />}
    </div>
  );
}
