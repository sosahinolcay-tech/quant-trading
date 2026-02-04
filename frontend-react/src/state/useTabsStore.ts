import { create } from "zustand";

type Tab = {
  id: string;
  title: string;
  view: "dashboard" | "chart" | "screener" | "strategies" | "portfolio" | "settings";
};

type TabState = {
  tabs: Tab[];
  activeTabId: string;
  setActiveTab: (id: string) => void;
  setActiveTabByView: (view: Tab["view"]) => void;
};

const initialTabs: Tab[] = [
  { id: "tab-dashboard", title: "Dashboard", view: "dashboard" },
  { id: "tab-chart", title: "Charts", view: "chart" },
  { id: "tab-screener", title: "Screener", view: "screener" },
  { id: "tab-strategies", title: "Strategies", view: "strategies" },
  { id: "tab-portfolio", title: "Portfolio", view: "portfolio" },
  { id: "tab-settings", title: "Settings", view: "settings" },
];

export const useTabsStore = create<TabState>((set, get) => ({
  tabs: initialTabs,
  activeTabId: initialTabs[0].id,
  setActiveTab: (id) => set({ activeTabId: id }),
  setActiveTabByView: (view) => {
    const tab = get().tabs.find((t) => t.view === view);
    if (tab) {
      set({ activeTabId: tab.id });
    }
  },
}));
