const base = 170;

export const mockPrices = Array.from({ length: 60 }).map((_, idx) => {
  const drift = Math.sin(idx / 5) * 2;
  const close = base + drift + idx * 0.05;
  const open = close - (Math.sin(idx / 3) * 0.6);
  const high = Math.max(open, close) + 0.8;
  const low = Math.min(open, close) - 0.9;
  const volume = 5000 + Math.round(Math.abs(Math.cos(idx / 4)) * 2500);
  return {
    timestamp: 1700000000 + idx * 86400,
    open,
    high,
    low,
    close,
    volume,
    ma20: close - 1.2,
    ma50: close - 2.4,
    rsi: 50 + Math.sin(idx / 4) * 10,
    macd: Math.sin(idx / 6) * 1.2,
    signal: Math.sin(idx / 7) * 1.0,
  };
});

export const mockIndicators = ["MA 20", "MA 50", "RSI", "MACD"];
