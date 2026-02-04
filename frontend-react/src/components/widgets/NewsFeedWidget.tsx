import { Skeleton } from "@/components/ui/Skeleton";
import { useNews } from "@/hooks/useNews";

export function NewsFeedWidget() {
  const { items, loading } = useNews();
  return (
    <div className="h-full p-2 flex flex-col">
      <div className="widget-handle mb-1.5 flex items-center justify-between">
        <div className="text-xs font-semibold">News Feed</div>
        <span className="text-[11px] text-muted">Macro · Equities</span>
      </div>
      <div className="flex-1 space-y-1.5 overflow-auto pr-1">
        {loading ? (
          <>
            <Skeleton className="h-3.5 w-full" />
            <Skeleton className="h-3.5 w-4/5" />
            <Skeleton className="h-3.5 w-3/5" />
          </>
        ) : items.length === 0 ? (
          <div className="text-xs text-muted">No news available.</div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="space-y-1 border-b border-border pb-2">
              <div className="text-xs leading-snug">{item.headline}</div>
              <div className="text-[11px] text-muted">
                {item.source} · {item.time}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
