import { useEffect, useState } from "react";
import { getJson } from "@/utils/api";

type NewsItem = {
  id: string;
  headline: string;
  source: string;
  time: string;
};

export function useNews() {
  const [items, setItems] = useState<NewsItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getJson<NewsItem[]>("/data/news")
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
