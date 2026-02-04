import RGL from "react-grid-layout";
import { useState } from "react";
import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { MarketOverview } from "@/components/widgets/MarketOverview";
import { HeatmapWidget } from "@/components/widgets/HeatmapWidget";
import { OhlcChartWidget } from "@/components/widgets/OhlcChartWidget";
import { VolumeProfileWidget } from "@/components/widgets/VolumeProfileWidget";
import { NewsFeedWidget } from "@/components/widgets/NewsFeedWidget";
import { SignalsWidget } from "@/components/widgets/SignalsWidget";
import { useLayoutStore } from "@/state/useLayoutStore";
import { useWidgetStore } from "@/state/useWidgetStore";

export function DashboardPage() {
  const { layouts, setLayouts } = useLayoutStore();
  const { getSymbol, setSymbol } = useWidgetStore();
  const current = layouts.lg ?? [];
  const [pickerOpen, setPickerOpen] = useState(false);

  const addWidget = (type: "market" | "chart" | "news" | "heatmap" | "volume" | "signals") => {
    const id = `${type}-${Date.now()}`;
    const sizeMap = {
      market: { w: 3, h: 3 },
      chart: { w: 4, h: 4 },
      news: { w: 3, h: 3 },
      heatmap: { w: 3, h: 3 },
      volume: { w: 4, h: 4 },
      signals: { w: 3, h: 3 },
    };
    const size = sizeMap[type];
    const next = [...current, { i: id, x: 0, y: Infinity, w: size.w, h: size.h }];
    setLayouts({ ...layouts, lg: next });
    if (type === "chart" || type === "volume") {
      setSymbol(id, "AAPL");
    }
    setPickerOpen(false);
  };

  const renderWidget = (id: string) => {
    const base = id.split("-")[0];
    if (id === "market" || base === "market") return <MarketOverview />;
    if (id === "chart" || base === "chart") {
      const key = id === "chart" ? "chart" : id;
      const symbol = getSymbol(key, "AAPL");
      return <OhlcChartWidget symbol={symbol} onSymbolChange={(next) => setSymbol(key, next)} />;
    }
    if (id === "news" || base === "news") return <NewsFeedWidget />;
    if (id === "heatmap" || base === "heatmap") return <HeatmapWidget />;
    if (id === "volume" || base === "volume") {
      const key = id === "volume" ? "volume" : id;
      const symbol = getSymbol(key, "AAPL");
      return (
        <VolumeProfileWidget symbol={symbol} onSymbolChange={(next) => setSymbol(key, next)} />
      );
    }
    if (id === "signals" || base === "signals") return <SignalsWidget />;
    return null;
  };

  return (
    <div className="flex h-full flex-col gap-3">
      <div className="flex items-center justify-between">
        <div className="text-sm font-semibold">Dashboard</div>
        <Button
          variant="ghost"
          className="h-8 px-2 text-xs"
          onClick={() => setPickerOpen(true)}
        >
          + Add widget
        </Button>
      </div>
      <RGL
        className="layout"
        layout={current}
        cols={12}
        rowHeight={40}
        width={1200}
        draggableHandle=".widget-handle"
        onLayoutChange={(next) => setLayouts({ lg: next })}
      >
        {current.map((item) => (
          <div key={item.i} className="rounded-xl bg-card shadow-soft border border-border">
            {renderWidget(item.i)}
          </div>
        ))}
      </RGL>
      <Modal open={pickerOpen} onClose={() => setPickerOpen(false)}>
        <div className="space-y-3">
          <div className="text-sm font-semibold">Add widget</div>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {[
              { id: "market", label: "Market Overview" },
              { id: "chart", label: "OHLC Chart" },
              { id: "news", label: "News Feed" },
              { id: "heatmap", label: "Heatmap" },
              { id: "volume", label: "Volume Profile" },
              { id: "signals", label: "Signals" },
            ].map((item) => (
              <button
                key={item.id}
                type="button"
                onClick={() =>
                  addWidget(item.id as "market" | "chart" | "news" | "heatmap" | "volume" | "signals")
                }
                className="rounded-lg border border-border bg-panel/60 px-3 py-2 text-left text-xs text-text hover:bg-white/5"
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      </Modal>
    </div>
  );
}
