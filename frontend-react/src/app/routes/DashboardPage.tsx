import { Responsive, WidthProvider } from "react-grid-layout";
import { MarketOverview } from "@/components/widgets/MarketOverview";
import { HeatmapWidget } from "@/components/widgets/HeatmapWidget";
import { OhlcChartWidget } from "@/components/widgets/OhlcChartWidget";
import { VolumeProfileWidget } from "@/components/widgets/VolumeProfileWidget";
import { NewsFeedWidget } from "@/components/widgets/NewsFeedWidget";
import { SignalsWidget } from "@/components/widgets/SignalsWidget";
import { useLayoutStore } from "@/state/useLayoutStore";

const ResponsiveGrid = WidthProvider(Responsive);

export function DashboardPage() {
  const { layouts, setLayouts } = useLayoutStore();

  return (
    <ResponsiveGrid
      className="layout"
      layouts={layouts}
      breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480 }}
      cols={{ lg: 12, md: 10, sm: 6, xs: 4 }}
      rowHeight={60}
      draggableHandle=".widget-handle"
      onLayoutChange={(_, next) => setLayouts(next)}
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
    </ResponsiveGrid>
  );
}
