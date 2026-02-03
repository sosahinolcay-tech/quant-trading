import type { SeriesPoint } from "@/utils/indicators";

export function toVolumeProfile(data: SeriesPoint[]) {
  if (!data.length) return [];
  const min = Math.min(...data.map((d) => d.low));
  const max = Math.max(...data.map((d) => d.high));
  if (max === min) {
    return [{ price: Math.round(max * 100) / 100, volume: data.reduce((s, p) => s + p.volume, 0) }];
  }
  const buckets = 6;
  const step = (max - min) / buckets;
  const profile = Array.from({ length: buckets }).map((_, idx) => ({
    price: Math.round((min + step * (idx + 1)) * 100) / 100,
    volume: 0,
  }));
  data.forEach((point) => {
    const idx = Math.min(
      buckets - 1,
      Math.max(0, Math.floor((point.close - min) / step))
    );
    profile[idx].volume += point.volume;
  });
  return profile;
}
