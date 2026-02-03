import { formatNumber, formatPercent } from "@/utils/format";
import { Tooltip } from "@/components/ui/Tooltip";
import { useMarketOverview } from "@/hooks/useMarketOverview";
import { Skeleton } from "@/components/ui/Skeleton";

export function MarketOverview() {
  const { items, loading } = useMarketOverview();
  return (
    <div className="h-full p-4">
      <div className="widget-handle flex items-center justify-between mb-3">
        <div className="text-sm font-semibold">Market Overview</div>
        <span className="text-xs text-muted">Live · US</span>
      </div>
      <div className="space-y-3">
        {loading ? (
          <>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-3/5" />
          </>
        ) : (
          items.map((item) => (
          <div key={item.symbol} className="flex items-center justify-between">
            <div>
              <div className="text-sm">{item.symbol}</div>
              <div className="text-xs text-muted">{item.name}</div>
            </div>
            <div className="text-right">
              <div className="text-sm">{formatNumber(item.price)}</div>
            <Tooltip label="Change since open">
              <div className={`text-xs ${item.change >= 0 ? "text-emerald-400" : "text-red-400"}`}>
                {formatPercent(item.change)}
              </div>
            </Tooltip>
            </div>
          </div>
          ))
        )}
      </div>
    </div>
  );
}
