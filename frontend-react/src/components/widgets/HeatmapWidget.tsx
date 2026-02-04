import { formatPercent } from "@/utils/format";
import { useHeatmap } from "@/hooks/useHeatmap";
import { Skeleton } from "@/components/ui/Skeleton";

export function HeatmapWidget() {
  const { tiles, loading } = useHeatmap();
  return (
    <div className="h-full p-2">
      <div className="widget-handle flex items-center justify-between mb-1.5">
        <div className="text-xs font-semibold">Sector Heatmap</div>
        <span className="text-[11px] text-muted">Top movers</span>
      </div>
      <div className="grid grid-cols-4 gap-1">
        {loading ? (
          Array.from({ length: 8 }).map((_, idx) => <Skeleton key={idx} className="h-9" />)
        ) : (
          tiles.map((tile) => (
          <div
            key={tile.symbol}
            className="rounded-lg border border-border px-2 py-1 text-[11px]"
            style={{
              background: tile.change >= 0 ? "rgba(16, 185, 129, 0.15)" : "rgba(239, 68, 68, 0.15)",
            }}
          >
            <div className="text-xs leading-tight">{tile.symbol}</div>
            <div className="text-muted">{formatPercent(tile.change)}</div>
          </div>
          ))
        )}
      </div>
    </div>
  );
}
