import { create } from "zustand";

type ChartState = {
  symbol: string;
  display: string;
  setSymbol: (symbol: string, display?: string) => void;
};

export const useChartStore = create<ChartState>((set) => ({
  symbol: "AAPL",
  display: "AAPL",
  setSymbol: (symbol, display) => set({ symbol, display: display ?? symbol }),
}));
