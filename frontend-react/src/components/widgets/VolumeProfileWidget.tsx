import { useState } from "react";
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip } from "recharts";
import { usePriceSeries } from "@/hooks/usePriceSeries";
import { toVolumeProfile } from "@/hooks/useVolumeProfile";

type VolumeProfileWidgetProps = {
  symbol: string;
  onSymbolChange?: (symbol: string) => void;
};

export function VolumeProfileWidget({ symbol, onSymbolChange }: VolumeProfileWidgetProps) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(symbol);
  const { data } = usePriceSeries(symbol, "1d");
  const profile = toVolumeProfile(data);
  const last = data[data.length - 1];
  return (
    <div className="h-full p-2">
      <div className="widget-handle mb-1.5 flex items-center justify-between gap-2">
        <div className="text-xs font-semibold">Volume Profile · {symbol}</div>
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
          <span className="text-[10px] text-muted">Last 30 sessions</span>
        </div>
      </div>
      {last && (
        <div className="mb-1 text-[11px] text-muted">Last {last.close.toFixed(2)}</div>
      )}
      <ResponsiveContainer width="100%" height={150}>
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
