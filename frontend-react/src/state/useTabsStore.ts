import { create } from "zustand";

type Tab = {
  id: string;
  title: string;
  view: "dashboard" | "chart";
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
