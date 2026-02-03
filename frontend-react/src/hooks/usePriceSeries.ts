import { useEffect, useState } from "react";
import { postJson } from "@/utils/api";
import type { PriceBar } from "@/utils/api";
import type { SeriesPoint } from "@/utils/indicators";

type PriceSeriesState = {
  data: SeriesPoint[];
  loading: boolean;
  error?: string;
};

const defaultRange = () => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 60);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
};

export function usePriceSeries(symbol: string, interval = "1d") {
  const [{ data, loading, error }, setState] = useState<PriceSeriesState>({
    data: [],
    loading: true,
  });

  useEffect(() => {
    let active = true;
    const { start, end } = defaultRange();
    setState({ data: [], loading: true });
    postJson<PriceBar[]>("/data/prices", { symbol, start, end, interval, source: "yahoo" })
      .then((rows) => {
        if (!active) return;
        const points = rows.map((row) => ({
          timestamp: row.timestamp,
          open: row.price_open,
          high: row.price_high,
          low: row.price_low,
          close: row.price_close,
          volume: row.volume,
        }));
        setState({ data: points, loading: false });
      })
      .catch((err) => {
        if (!active) return;
        setState({ data: [], loading: false, error: err.message });
      });
    return () => {
      active = false;
    };
  }, [symbol, interval]);

  return { data, loading, error };
}
