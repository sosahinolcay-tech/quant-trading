import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
import { usePriceSeries } from "@/hooks/usePriceSeries";
import { toVolumeProfile } from "@/hooks/useVolumeProfile";

export function VolumeProfileWidget() {
  const { data } = usePriceSeries("AAPL", "1d");
  const profile = toVolumeProfile(data);
  return (
    <div className="h-full p-4">
      <div className="widget-handle mb-3 flex items-center justify-between">
        <div className="text-sm font-semibold">Volume Profile</div>
        <span className="text-xs text-muted">Last 30 sessions</span>
      </div>
      <ResponsiveContainer width="100%" height={220}>
        <BarChart data={profile}>
          <XAxis dataKey="price" tick={{ fill: "#A7B0C0", fontSize: 10 }} />
          <YAxis hide />
          <Tooltip
            cursor={{ fill: "rgba(255,255,255,0.04)" }}
            contentStyle={{ background: "#0F1424", border: "1px solid rgba(255,255,255,0.08)" }}
          />
          <Bar dataKey="volume" fill="#7C5CFF" radius={[6, 6, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
