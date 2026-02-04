import { useMemo, useState } from "react";
import {
  ResponsiveContainer,
  LineChart,
  Line,
  AreaChart,
  Area,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { TabButton } from "@/components/ui/TabButton";
import { Tooltip as Hint } from "@/components/ui/Tooltip";
import { usePriceSeries } from "@/hooks/usePriceSeries";
import type { SeriesPoint } from "@/utils/indicators";
import { movingAverage } from "@/utils/indicators";
import { cn, formatNumber, formatPercent } from "@/utils/format";

type StrategyId = "market_maker" | "pairs_trading";

type ParamSpec = {
  key: string;
  label: string;
  description: string;
  min: number;
  max: number;
  step: number;
  unit?: string;
};

const paramGroups: Record<StrategyId, Array<{ title: string; fields: ParamSpec[] }>> = {
  market_maker: [
    {
      title: "Volatility",
      fields: [
        {
          key: "targetVol",
          label: "Target volatility",
          description: "Annualized realized volatility target",
          min: 0.1,
          max: 0.8,
          step: 0.01,
          unit: "%",
        },
        {
          key: "spreadWidth",
          label: "Quote spread",
          description: "Base spread around mid price",
          min: 0.02,
          max: 0.4,
          step: 0.01,
        },
      ],
    },
    {
      title: "Inventory",
      fields: [
        {
          key: "inventoryCap",
          label: "Inventory cap",
          description: "Maximum base inventory exposure",
          min: 10,
          max: 250,
          step: 5,
        },
        {
          key: "inventoryPenalty",
          label: "Inventory penalty",
          description: "Aggressiveness of inventory skew",
          min: 0.1,
          max: 2.0,
          step: 0.1,
        },
      ],
    },
    {
      title: "Risk",
      fields: [
        {
          key: "riskLimit",
          label: "Risk limit",
          description: "Daily risk budget",
          min: 1000,
          max: 10000,
          step: 250,
          unit: "$",
        },
        {
          key: "stopLoss",
          label: "Stop loss",
          description: "Hard stop for strategy drawdown",
          min: 0.5,
          max: 8.0,
          step: 0.5,
          unit: "%",
        },
      ],
    },
  ],
  pairs_trading: [
    {
      title: "Signal",
      fields: [
        {
          key: "zEntry",
          label: "Z-entry threshold",
          description: "Entry threshold for spread deviation",
          min: 0.5,
          max: 3.5,
          step: 0.1,
        },
        {
          key: "zExit",
          label: "Z-exit threshold",
          description: "Mean-reversion exit trigger",
          min: 0.1,
          max: 1.5,
          step: 0.1,
        },
      ],
    },
    {
      title: "Inventory",
      fields: [
        {
          key: "positionSize",
          label: "Position size",
          description: "Notional per leg",
          min: 10000,
          max: 100000,
          step: 5000,
          unit: "$",
        },
        {
          key: "maxPairs",
          label: "Concurrent pairs",
          description: "Maximum open pairs",
          min: 1,
          max: 10,
          step: 1,
        },
      ],
    },
    {
      title: "Risk",
      fields: [
        {
          key: "correlationMin",
          label: "Min correlation",
          description: "Rolling correlation filter",
          min: 0.4,
          max: 0.95,
          step: 0.05,
        },
        {
          key: "cooldown",
          label: "Cooldown (bars)",
          description: "Minimum bars between trades",
          min: 1,
          max: 15,
          step: 1,
        },
      ],
    },
  ],
};

const defaults = {
  market_maker: {
    targetVol: 0.35,
    spreadWidth: 0.12,
    inventoryCap: 120,
    inventoryPenalty: 0.9,
    riskLimit: 4500,
    stopLoss: 2.5,
  },
  pairs_trading: {
    zEntry: 2.1,
    zExit: 0.7,
    positionSize: 40000,
    maxPairs: 4,
    correlationMin: 0.7,
    cooldown: 5,
  },
};

const std = (values: number[]) => {
  if (values.length < 2) return 0;
  const mean = values.reduce((sum, val) => sum + val, 0) / values.length;
  const variance =
    values.reduce((sum, val) => sum + (val - mean) ** 2, 0) / (values.length - 1);
  return Math.sqrt(variance);
};

const buildDrawdown = (series: Array<{ x: number; y: number }>) => {
  let peak = -Infinity;
  return series.map((point) => {
    peak = Math.max(peak, point.y);
    return { x: point.x, y: Math.min(0, point.y - peak) };
  });
};

const buildMarketMakerPnL = (
  data: SeriesPoint[],
  params: typeof defaults.market_maker
) => {
  if (data.length < 30) return { series: [], trades: 0, returns: [] as number[] };
  const ma20 = movingAverage(data, 20);
  const entry = Math.max(0.5, params.spreadWidth * 6);
  let position = 0;
  let pnl = 0;
  let trades = 0;
  const series: Array<{ x: number; y: number }> = [];
  const returns: number[] = [];
  for (let i = 1; i < data.length; i += 1) {
    const ma = ma20[i];
    if (!ma) continue;
    const window = data.slice(Math.max(0, i - 20), i + 1).map((p) => p.close);
    const z = std(window) === 0 ? 0 : (data[i].close - ma) / std(window);
    const prev = position;
    if (z > entry) position = -1;
    if (z < -entry) position = 1;
    if (Math.abs(z) < entry / 2) position = 0;
    if (prev !== position) trades += 1;
    const ret = (data[i].close - data[i - 1].close) / data[i - 1].close;
    const scaled = ret * (params.targetVol * 8);
    pnl += position * scaled;
    returns.push(position * scaled);
    series.push({ x: data[i].timestamp, y: pnl });
  }
  return { series, trades, returns };
};

const buildPairsPnL = (
  a: SeriesPoint[],
  b: SeriesPoint[],
  params: typeof defaults.pairs_trading
) => {
  const mapB = new Map(b.map((point) => [point.timestamp, point.close]));
  const aligned = a
    .filter((point) => mapB.has(point.timestamp))
    .map((point) => ({
      timestamp: point.timestamp,
      a: point.close,
      b: mapB.get(point.timestamp) ?? point.close,
    }));
  if (aligned.length < 30) return { series: [], trades: 0, returns: [] as number[] };
  const spread = aligned.map((point) => Math.log(point.a) - Math.log(point.b));
  let position = 0;
  let pnl = 0;
  let trades = 0;
  const series: Array<{ x: number; y: number }> = [];
  const returns: number[] = [];
  for (let i = 1; i < spread.length; i += 1) {
    const window = spread.slice(Math.max(0, i - 20), i + 1);
    const z = std(window) === 0 ? 0 : (spread[i] - window.reduce((s, v) => s + v, 0) / window.length) / std(window);
    const prev = position;
    if (z > params.zEntry) position = -1;
    if (z < -params.zEntry) position = 1;
    if (Math.abs(z) < params.zExit) position = 0;
    if (prev !== position) trades += 1;
    const ret = spread[i] - spread[i - 1];
    const scaled = ret * (params.positionSize / 100000);
    pnl += position * scaled;
    returns.push(position * scaled);
    series.push({ x: aligned[i].timestamp, y: pnl });
  }
  return { series, trades, returns };
};

export function StrategiesPage() {
  const [active, setActive] = useState<StrategyId>("market_maker");
  const [params, setParams] = useState({
    market_maker: { ...defaults.market_maker },
    pairs_trading: { ...defaults.pairs_trading },
  });
  const [running, setRunning] = useState(false);
  const [log, setLog] = useState<string[]>(["Loaded market data window."]);
  const aapl = usePriceSeries("AAPL", "1d");
  const msft = usePriceSeries("MSFT", "1d");

  const activeParams = params[active];
  const groups = paramGroups[active];

  const result = useMemo(() => {
    if (active === "pairs_trading") {
      return buildPairsPnL(aapl.data, msft.data, params.pairs_trading);
    }
    return buildMarketMakerPnL(aapl.data, params.market_maker);
  }, [active, aapl.data, msft.data, params.market_maker, params.pairs_trading]);

  const drawdownSeries = useMemo(() => buildDrawdown(result.series), [result.series]);

  const metrics = useMemo(() => {
    if (!result.returns.length) {
      return { sharpe: 0, maxDrawdown: 0, trades: 0, winRate: 0 };
    }
    const mean = result.returns.reduce((sum, val) => sum + val, 0) / result.returns.length;
    const sigma = std(result.returns);
    const sharpe = sigma === 0 ? 0 : (mean / sigma) * Math.sqrt(252);
    const wins = result.returns.filter((val) => val > 0).length;
    const winRate = wins / result.returns.length;
    const maxDrawdown = Math.min(...drawdownSeries.map((point) => point.y), 0);
    return { sharpe, maxDrawdown, trades: result.trades, winRate };
  }, [drawdownSeries, result.returns, result.trades]);

  const handleRun = () => {
    if (running) return;
    setRunning(true);
    setLog((prev) => [
      `Started ${active === "market_maker" ? "Market Maker" : "Pairs Trading"} backtest.`,
      ...prev,
    ]);
    window.setTimeout(() => {
      setRunning(false);
      setLog((prev) => [
        `Completed run · Sharpe ${metrics.sharpe.toFixed(2)} · Trades ${metrics.trades}`,
        ...prev,
      ]);
    }, 900);
  };

  const loading = aapl.loading || (active === "pairs_trading" && msft.loading);

  return (
    <div className="flex h-full flex-col gap-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-sm font-semibold">Research & Execution</div>
          <div className="text-xs text-muted">Configure → run → evaluate</div>
        </div>
        <div className="flex gap-2">
          <TabButton
            label="Market Maker"
            active={active === "market_maker"}
            onClick={() => setActive("market_maker")}
          />
          <TabButton
            label="Pairs Trading"
            active={active === "pairs_trading"}
            onClick={() => setActive("pairs_trading")}
          />
        </div>
      </div>

      <div className="grid flex-1 grid-cols-[280px_1fr] gap-4">
        <Card className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="text-sm font-semibold">Parameters</div>
            <button
              type="button"
              onClick={() =>
                setParams((prev) => ({
                  ...prev,
                  [active]: { ...defaults[active] },
                }))
              }
              className="text-xs text-muted hover:text-text focus-visible:ring-2 focus-visible:ring-accent/60"
            >
              Reset defaults
            </button>
          </div>
          {groups.map((group) => (
            <div key={group.title} className="space-y-3">
              <div className="text-xs uppercase text-muted">{group.title}</div>
              {group.fields.map((field) => {
                const value = activeParams[field.key as keyof typeof activeParams] as number;
                return (
                  <div key={field.key} className="space-y-1">
                    <Hint label={field.description}>
                      <div className="flex items-center justify-between text-xs text-muted">
                        <span>{field.label}</span>
                        <span className="font-semibold text-text">
                          {field.unit === "%"
                            ? formatPercent(value * 100)
                            : field.unit === "$"
                            ? formatNumber(value)
                            : formatNumber(value)}
                        </span>
                      </div>
                    </Hint>
                    <input
                      type="range"
                      min={field.min}
                      max={field.max}
                      step={field.step}
                      value={value}
                      onChange={(event) =>
                        setParams((prev) => ({
                          ...prev,
                          [active]: {
                            ...prev[active],
                            [field.key]: Number(event.target.value),
                          },
                        }))
                      }
                      className="w-full accent-accent focus-visible:ring-2 focus-visible:ring-accent/60"
                    />
                  </div>
                );
              })}
            </div>
          ))}
        </Card>

        <Card className="flex flex-col gap-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm font-semibold">Results Canvas</div>
              <div className="text-xs text-muted">PnL, drawdown, and key metrics</div>
            </div>
            <Button onClick={handleRun} disabled={running || loading}>
              {running ? "Running…" : "Run / Backtest"}
            </Button>
          </div>

          <div className="grid flex-1 grid-cols-2 gap-4">
            <div className="rounded-xl border border-border bg-panel/50 p-3">
              <div className="text-xs text-muted">PnL curve</div>
              <div className="mt-2 h-48">
                {running || loading ? (
                  <Skeleton className="h-full w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={result.series}>
                      <XAxis dataKey="x" hide />
                      <YAxis hide />
                      <Tooltip
                        cursor={{ stroke: "rgba(255,255,255,0.1)" }}
                        contentStyle={{
                          background: "#0F1424",
                          border: "1px solid rgba(255,255,255,0.08)",
                        }}
                      />
                      <Line type="monotone" dataKey="y" stroke="#7C5CFF" dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>

            <div className="rounded-xl border border-border bg-panel/50 p-3">
              <div className="text-xs text-muted">Drawdown</div>
              <div className="mt-2 h-48">
                {running || loading ? (
                  <Skeleton className="h-full w-full" />
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={drawdownSeries}>
                      <XAxis dataKey="x" hide />
                      <YAxis hide />
                      <Tooltip
                        cursor={{ stroke: "rgba(255,255,255,0.1)" }}
                        contentStyle={{
                          background: "#0F1424",
                          border: "1px solid rgba(255,255,255,0.08)",
                        }}
                      />
                      <Area type="monotone" dataKey="y" stroke="#FF6B6B" fill="#FF6B6B33" />
                    </AreaChart>
                  </ResponsiveContainer>
                )}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-4 gap-3">
            {running || loading ? (
              <>
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
                <Skeleton className="h-16 w-full" />
              </>
            ) : (
              [
                { label: "Sharpe", value: metrics.sharpe.toFixed(2) },
                { label: "Max drawdown", value: formatPercent(metrics.maxDrawdown * 100) },
                { label: "Trades", value: metrics.trades.toString() },
                { label: "Win rate", value: formatPercent(metrics.winRate * 100) },
              ].map((metric) => (
                <div
                  key={metric.label}
                  className={cn("rounded-xl border border-border bg-panel/60 p-3")}
                >
                  <div className="text-xs text-muted">{metric.label}</div>
                  <div className="text-sm font-semibold">{metric.value}</div>
                </div>
              ))
            )}
          </div>
        </Card>
      </div>

      <Card className="h-32 overflow-auto">
        <div className="mb-2 text-xs uppercase text-muted">Execution log</div>
        <div className="space-y-1 text-xs text-muted">
          {log.map((entry, index) => (
            <div key={`${entry}-${index}`}>{entry}</div>
          ))}
        </div>
      </Card>
    </div>
  );
}
