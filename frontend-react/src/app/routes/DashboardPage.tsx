import RGL from "react-grid-layout";
import { MarketOverview } from "@/components/widgets/MarketOverview";
import { HeatmapWidget } from "@/components/widgets/HeatmapWidget";
import { OhlcChartWidget } from "@/components/widgets/OhlcChartWidget";
import { VolumeProfileWidget } from "@/components/widgets/VolumeProfileWidget";
import { NewsFeedWidget } from "@/components/widgets/NewsFeedWidget";
import { SignalsWidget } from "@/components/widgets/SignalsWidget";
import { useLayoutStore } from "@/state/useLayoutStore";

export function DashboardPage() {
  const { layouts, setLayouts } = useLayoutStore();

  return (
    <RGL
      className="layout"
      layout={layouts.lg}
      cols={12}
      rowHeight={60}
      width={1200}
      draggableHandle=".widget-handle"
      onLayoutChange={(next) => setLayouts({ lg: next })}
    >
      <div key="market" className="rounded-xl bg-card shadow-soft border border-border">
        <MarketOverview />
      </div>
      <div key="chart" className="rounded-xl bg-card shadow-soft border border-border">
        <OhlcChartWidget />
      </div>
      <div key="news" className="rounded-xl bg-card shadow-soft border border-border">
        <NewsFeedWidget />
      </div>
      <div key="heatmap" className="rounded-xl bg-card shadow-soft border border-border">
        <HeatmapWidget />
      </div>
      <div key="volume" className="rounded-xl bg-card shadow-soft border border-border">
        <VolumeProfileWidget />
      </div>
      <div key="signals" className="rounded-xl bg-card shadow-soft border border-border">
        <SignalsWidget />
      </div>
    </RGL>
  );
}
