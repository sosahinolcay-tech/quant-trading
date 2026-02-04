import { create } from "zustand";

type WidgetState = {
  symbols: Record<string, string>;
  setSymbol: (widgetId: string, symbol: string) => void;
  getSymbol: (widgetId: string, fallback: string) => string;
};

export const useWidgetStore = create<WidgetState>((set, get) => ({
  symbols: {},
  setSymbol: (widgetId, symbol) =>
    set((state) => ({ symbols: { ...state.symbols, [widgetId]: symbol } })),
  getSymbol: (widgetId, fallback) => get().symbols[widgetId] ?? fallback,
}));
