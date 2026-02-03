type IndicatorLegendProps = {
  indicators: string[];
};

export function IndicatorLegend({ indicators }: IndicatorLegendProps) {
  return (
    <div className="flex items-center gap-3 text-xs text-muted">
      {indicators.map((indicator) => (
        <span key={indicator} className="rounded-full border border-border px-2 py-1">
          {indicator}
        </span>
      ))}
    </div>
  );
}
