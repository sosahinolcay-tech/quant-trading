import { Skeleton } from "@/components/ui/Skeleton";
import { useNews } from "@/hooks/useNews";

export function NewsFeedWidget() {
  const { items, loading } = useNews();
  return (
    <div className="h-full p-4">
      <div className="widget-handle mb-3 flex items-center justify-between">
        <div className="text-sm font-semibold">News Feed</div>
        <span className="text-xs text-muted">Macro · Equities</span>
      </div>
      <div className="space-y-3">
        {loading ? (
          <>
            <Skeleton className="h-4 w-full" />
            <Skeleton className="h-4 w-4/5" />
            <Skeleton className="h-4 w-3/5" />
          </>
        ) : items.length === 0 ? (
          <div className="text-sm text-muted">No news available.</div>
        ) : (
          items.map((item) => (
            <div key={item.id} className="space-y-1 border-b border-border pb-2">
              <div className="text-sm">{item.headline}</div>
              <div className="text-xs text-muted">
                {item.source} · {item.time}
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
