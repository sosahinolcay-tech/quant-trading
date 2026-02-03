import type { ReactNode } from "react";
import { DashboardPage } from "@/app/routes/DashboardPage";
import { ChartPage } from "@/app/routes/ChartPage";
import { TabButton } from "@/components/ui/TabButton";
import { useTabsStore } from "@/state/useTabsStore";

const viewMap: Record<string, ReactNode> = {
  dashboard: <DashboardPage />,
  chart: <ChartPage />,
};

export function TabWorkspace() {
  const { tabs, activeTabId, setActiveTab } = useTabsStore();

  const active = tabs.find((tab) => tab.id === activeTabId) ?? tabs[0];

  return (
    <div className="h-full flex flex-col">
      <div className="flex items-center gap-2 border-b border-border bg-card px-4 py-2">
        {tabs.map((tab) => (
          <TabButton
            key={tab.id}
            label={tab.title}
            active={tab.id === activeTabId}
            onClick={() => setActiveTab(tab.id)}
          />
        ))}
      </div>
      <div className="flex-1 overflow-auto p-4">
        {active ? viewMap[active.view] : null}
      </div>
    </div>
  );
}
