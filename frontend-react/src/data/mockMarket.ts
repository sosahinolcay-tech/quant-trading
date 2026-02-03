export const mockMarketOverview = [
  { symbol: "SPX", name: "S&P 500", price: 5128.4, change: 0.42 },
  { symbol: "NDX", name: "Nasdaq 100", price: 18212.6, change: -0.18 },
  { symbol: "DXY", name: "Dollar Index", price: 103.2, change: 0.07 },
  { symbol: "VIX", name: "Volatility", price: 14.2, change: -0.9 },
];

export const mockHeatmap = [
  { symbol: "AAPL", change: 0.8 },
  { symbol: "MSFT", change: 0.5 },
  { symbol: "NVDA", change: -1.2 },
  { symbol: "AMZN", change: 0.3 },
  { symbol: "META", change: -0.6 },
  { symbol: "TSLA", change: 1.4 },
  { symbol: "NFLX", change: 0.1 },
  { symbol: "GOOGL", change: -0.3 },
];

export const mockVolumeProfile = [
  { price: 168, volume: 3200 },
  { price: 169, volume: 4200 },
  { price: 170, volume: 5800 },
  { price: 171, volume: 5200 },
  { price: 172, volume: 4100 },
  { price: 173, volume: 2900 },
];

export const mockSignals = [
  { id: "sig-1", symbol: "AAPL", strategy: "Mean Reversion", side: "BUY", confidence: 76 },
  { id: "sig-2", symbol: "MSFT", strategy: "Momentum", side: "SELL", confidence: 64 },
  { id: "sig-3", symbol: "NVDA", strategy: "Volatility Breakout", side: "BUY", confidence: 71 },
];

export const mockOrderFlow = [
  { id: "flow-1", symbol: "AAPL", side: "BUY", price: 172.12, size: 3200 },
  { id: "flow-2", symbol: "AAPL", side: "SELL", price: 171.88, size: 2100 },
  { id: "flow-3", symbol: "AAPL", side: "BUY", price: 172.35, size: 1500 },
  { id: "flow-4", symbol: "AAPL", side: "SELL", price: 171.55, size: 900 },
];
