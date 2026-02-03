import { useEffect, useState } from "react";
import { getMarketStatus } from "@/utils/time";

export function MarketStatusIndicator() {
  const [status, setStatus] = useState(getMarketStatus());

  useEffect(() => {
    const id = setInterval(() => setStatus(getMarketStatus()), 60000);
    return () => clearInterval(id);
  }, []);
  return (
    <div className="flex items-center gap-2 rounded-xl border border-border bg-card px-3 py-2 text-xs">
      <span
        className={`h-2 w-2 rounded-full ${
          status === "open" ? "bg-emerald-400" : "bg-amber-400"
        }`}
      />
      <span className="uppercase tracking-wide text-muted">
        Market {status === "open" ? "Open" : "Closed"}
      </span>
    </div>
  );
}
