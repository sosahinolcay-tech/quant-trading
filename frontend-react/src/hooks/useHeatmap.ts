import { useEffect, useState } from "react";
import { postJson } from "@/utils/api";
import type { PriceBar } from "@/utils/api";

type HeatmapTile = {
  symbol: string;
  change: number;
};

const symbols = ["AAPL", "MSFT", "NVDA", "AMZN", "META", "TSLA", "NFLX", "GOOGL"];

const defaultRange = () => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 30);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
};

export function useHeatmap() {
  const [tiles, setTiles] = useState<HeatmapTile[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const { start, end } = defaultRange();
    Promise.all(
      symbols.map(async (symbol) => {
        const rows = await postJson<PriceBar[]>("/data/prices", {
          symbol,
          start,
          end,
          interval: "1d",
          source: "yahoo",
        });
        if (!rows.length) {
          return { symbol, change: 0 };
        }
        const last = rows[rows.length - 1];
        const prev = rows[rows.length - 2] || last;
        const change = ((last.price_close - prev.price_close) / prev.price_close) * 100;
        return { symbol, change };
      })
    )
      .then((data) => {
        if (active) setTiles(data);
        if (active) setLoading(false);
      })
      .catch(() => {
        if (active) setTiles([]);
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return { tiles, loading };
}
