export type PriceBar = {
  symbol: string;
  timestamp: number;
  price_open: number;
  price_high: number;
  price_low: number;
  price_close: number;
  volume: number;
  source: string;
};

const defaultBase = "http://127.0.0.1:8010";
const envBase = import.meta.env.VITE_API_BASE as string | undefined;

export const API_BASE = (envBase || defaultBase).replace(/\/+$/, "");

export async function postJson<T>(path: string, payload: unknown): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const text = await res.text();
    throw new Error(text || `Request failed: ${res.status}`);
  }
  return res.json() as Promise<T>;
}
