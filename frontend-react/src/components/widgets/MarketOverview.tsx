import { formatNumber, formatPercent } from "@/utils/format";
import { Tooltip } from "@/components/ui/Tooltip";
import { useMarketOverview } from "@/hooks/useMarketOverview";
import { Skeleton } from "@/components/ui/Skeleton";

export function MarketOverview() {
  const { items, loading } = useMarketOverview();
  return (
    <div className="h-full p-2">
      <div className="widget-handle flex items-center justify-between mb-1.5">
        <div className="text-xs font-semibold">Market Overview</div>
        <span className="text-[11px] text-muted">Live · US</span>
      </div>
      <div className="space-y-1.5">
        {loading ? (
          <>
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-4/5" />
            <Skeleton className="h-3.5 w-3/5" />
          </>
        ) : (
          items.map((item) => {
            const changeValue =
              item.change === 0 ? 0 : item.price - item.price / (1 + item.change / 100);
            return (
              <div key={item.symbol} className="flex items-center justify-between">
                <div>
                  <div className="text-sm">{item.symbol}</div>
                  <div className="text-[11px] text-muted">{item.name}</div>
                </div>
                <div className="text-right">
                  <div className="text-sm">{formatNumber(item.price)}</div>
                  <Tooltip label="Change since open">
                    <div
                      className={`text-[11px] ${item.change >= 0 ? "text-emerald-400" : "text-red-400"}`}
                    >
                      {formatPercent(item.change)} · {formatNumber(changeValue)}
                    </div>
                  </Tooltip>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
