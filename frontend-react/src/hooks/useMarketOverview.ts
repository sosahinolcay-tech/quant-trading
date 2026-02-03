import { useEffect, useState } from "react";
import { postJson } from "@/utils/api";
import type { PriceBar } from "@/utils/api";

type OverviewItem = {
  symbol: string;
  name: string;
  price: number;
  change: number;
};

const symbols = [
  { symbol: "SPY", name: "S&P 500 ETF" },
  { symbol: "QQQ", name: "Nasdaq 100 ETF" },
  { symbol: "DIA", name: "Dow 30 ETF" },
  { symbol: "IWM", name: "Russell 2000 ETF" },
];

const defaultRange = () => {
  const end = new Date();
  const start = new Date();
  start.setDate(end.getDate() - 30);
  return {
    start: start.toISOString().slice(0, 10),
    end: end.toISOString().slice(0, 10),
  };
};

export function useMarketOverview() {
  const [items, setItems] = useState<OverviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    const { start, end } = defaultRange();
    Promise.all(
      symbols.map(async (item) => {
        const rows = await postJson<PriceBar[]>("/data/prices", {
          symbol: item.symbol,
          start,
          end,
          interval: "1d",
          source: "yahoo",
        });
        if (!rows.length) {
          return { ...item, price: 0, change: 0 };
        }
        const last = rows[rows.length - 1];
        const prev = rows[rows.length - 2] || last;
        const change = ((last.price_close - prev.price_close) / prev.price_close) * 100;
        return { ...item, price: last.price_close, change };
      })
    )
      .then((data) => {
        if (active) setItems(data);
        if (active) setLoading(false);
      })
      .catch(() => {
        if (active) setItems([]);
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  return { items, loading };
}
