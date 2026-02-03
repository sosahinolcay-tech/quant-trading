import { create } from "zustand";
import type { Layout, Layouts } from "react-grid-layout";

const STORAGE_KEY = "qt-layouts-v1";

type LayoutState = {
  layouts: Layouts;
  setLayouts: (layouts: Layouts) => void;
};

const defaultLayouts: Layouts = {
  lg: [
    { i: "market", x: 0, y: 0, w: 3, h: 4 },
    { i: "chart", x: 3, y: 0, w: 6, h: 8 },
    { i: "news", x: 9, y: 0, w: 3, h: 6 },
    { i: "heatmap", x: 0, y: 4, w: 4, h: 4 },
    { i: "volume", x: 4, y: 8, w: 4, h: 4 },
    { i: "signals", x: 8, y: 6, w: 4, h: 4 },
  ],
};

function loadLayouts(): Layouts {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return defaultLayouts;
    return JSON.parse(raw) as Layouts;
  } catch {
    return defaultLayouts;
  }
}

export const useLayoutStore = create<LayoutState>((set) => ({
  layouts: loadLayouts(),
  setLayouts: (layouts) => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(layouts));
    set({ layouts });
  },
}));
