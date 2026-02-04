import clsx from "clsx";

export function cn(...inputs: Array<string | undefined | false>) {
  return clsx(inputs);
}

export function formatNumber(value: number) {
  return new Intl.NumberFormat("en-US", { maximumFractionDigits: 2 }).format(value);
}

export function formatCurrency(value: number) {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatPercent(value: number) {
  return `${value >= 0 ? "+" : ""}${value.toFixed(2)}%`;
}

export function formatTimestamp(value: number) {
  const date = new Date(value * 1000);
  return date.toLocaleDateString("en-US", { month: "short", day: "numeric" });
}

export function formatTime(value: number) {
  const date = new Date(value * 1000);
  return date.toLocaleTimeString("en-US", { hour: "2-digit", minute: "2-digit", hour12: false });
}

export function formatTimestampWithTime(value: number) {
  const date = new Date(value * 1000);
  return date.toLocaleString("en-US", {
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  });
}
