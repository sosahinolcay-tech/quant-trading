export type SeriesPoint = {
  timestamp: number;
  close: number;
  open: number;
  high: number;
  low: number;
  volume: number;
};

export function movingAverage(data: SeriesPoint[], window: number) {
  return data.map((point, idx) => {
    if (idx < window - 1) return null;
    const slice = data.slice(idx - window + 1, idx + 1);
    const avg = slice.reduce((sum, p) => sum + p.close, 0) / window;
    return avg;
  });
}

export function rsi(data: SeriesPoint[], period = 14) {
  const values: Array<number | null> = [];
  if (data.length < 2) {
    return Array(data.length).fill(null);
  }
  let gains = 0;
  let losses = 0;
  for (let i = 1; i < data.length; i += 1) {
    const diff = data[i].close - data[i - 1].close;
    if (i <= period) {
      gains += diff > 0 ? diff : 0;
      losses += diff < 0 ? -diff : 0;
      values.push(null);
    } else if (i === period + 1) {
      const rs = gains / (losses || 1);
      values.push(100 - 100 / (1 + rs));
    } else {
      const gain = diff > 0 ? diff : 0;
      const loss = diff < 0 ? -diff : 0;
      gains = (gains * (period - 1) + gain) / period;
      losses = (losses * (period - 1) + loss) / period;
      const rs = gains / (losses || 1);
      values.push(100 - 100 / (1 + rs));
    }
  }
  values.unshift(null);
  return values;
}

export function ema(values: number[], span: number) {
  if (!values.length) return [];
  const k = 2 / (span + 1);
  const result: number[] = [];
  let prev = values[0];
  result.push(prev);
  for (let i = 1; i < values.length; i += 1) {
    const next = values[i] * k + prev * (1 - k);
    result.push(next);
    prev = next;
  }
  return result;
}

export function macd(data: SeriesPoint[]) {
  const closes = data.map((p) => p.close);
  if (!closes.length) return { macd: [], signal: [] };
  const fast = ema(closes, 12);
  const slow = ema(closes, 26);
  const macdLine = fast.map((v, i) => v - slow[i]);
  const signal = ema(macdLine, 9);
  return { macd: macdLine, signal };
}
