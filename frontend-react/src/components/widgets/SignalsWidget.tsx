import { usePriceSeries } from "@/hooks/usePriceSeries";
import { movingAverage } from "@/utils/indicators";

export function SignalsWidget() {
  const aapl = usePriceSeries("AAPL", "1d");
  const msft = usePriceSeries("MSFT", "1d");

  const buildSignal = (symbol: string, data: ReturnType<typeof usePriceSeries>["data"]) => {
    if (!data.length) return null;
    const ma20 = movingAverage(data, 20);
    const last = data[data.length - 1];
    const avg = ma20[ma20.length - 1] ?? last.close;
    const side = last.close >= avg ? "BUY" : "SELL";
    const confidence = Math.min(99, Math.max(50, Math.abs((last.close - avg) / last.close) * 100));
    return { symbol, strategy: "Trend Filter", side, confidence: Math.round(confidence) };
  };

  const signals = [
    buildSignal("AAPL", aapl.data),
    buildSignal("MSFT", msft.data),
  ].filter(Boolean) as Array<{ symbol: string; strategy: string; side: string; confidence: number }>;

  return (
    <div className="h-full p-2">
      <div className="widget-handle mb-1.5 flex items-center justify-between">
        <div className="text-xs font-semibold">Strategy Signals</div>
        <span className="text-[11px] text-muted">Intraday</span>
      </div>
      <div className="space-y-1.5">
        {signals.length === 0 ? (
          <div className="text-xs text-muted">Loading signals...</div>
        ) : (
          signals.map((signal) => (
          <div key={signal.symbol} className="flex items-center justify-between">
            <div>
              <div className="text-sm">{signal.symbol}</div>
              <div className="text-[11px] text-muted">{signal.strategy}</div>
            </div>
            <div className={`text-[11px] ${signal.side === "BUY" ? "text-emerald-400" : "text-red-400"}`}>
              {signal.side} · {signal.confidence}%
            </div>
          </div>
          ))
        )}
      </div>
    </div>
  );
}
