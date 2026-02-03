import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis, ComposedChart } from "recharts";
import type { SeriesPoint } from "@/utils/indicators";
import { formatTimestamp } from "@/utils/format";

type IndicatorPanelsProps = {
  data: Array<SeriesPoint & { rsi?: number | null; macd?: number; signal?: number }>;
};

export function IndicatorPanels({ data }: IndicatorPanelsProps) {
  return (
    <div className="mt-4 grid grid-cols-2 gap-4">
      <div className="h-40 rounded-xl border border-border bg-panel p-3">
        <div className="text-xs text-muted mb-2">RSI (14)</div>
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} hide />
            <YAxis domain={[0, 100]} tick={{ fill: "#A7B0C0", fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "#0F1424", border: "1px solid rgba(255,255,255,0.08)" }} />
            <Line type="monotone" dataKey="rsi" stroke="#5CE1E6" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="h-40 rounded-xl border border-border bg-panel p-3">
        <div className="text-xs text-muted mb-2">MACD</div>
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={data}>
            <XAxis dataKey="timestamp" tickFormatter={formatTimestamp} hide />
            <YAxis tick={{ fill: "#A7B0C0", fontSize: 10 }} />
            <Tooltip contentStyle={{ background: "#0F1424", border: "1px solid rgba(255,255,255,0.08)" }} />
            <Line type="monotone" dataKey="macd" stroke="#7C5CFF" dot={false} />
            <Line type="monotone" dataKey="signal" stroke="#F97316" dot={false} />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
