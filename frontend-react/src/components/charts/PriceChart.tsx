import {
  Brush,
  ComposedChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
  Line,
  Customized,
} from "recharts";
import { formatCurrency, formatTimestamp } from "@/utils/format";
import type { SeriesPoint } from "@/utils/indicators";

type PriceChartProps = {
  height?: number;
  data?: SeriesPoint[];
};

export function PriceChart({ height = 360, data = [] }: PriceChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data}>
        <XAxis
          dataKey="timestamp"
          tickFormatter={formatTimestamp}
          tick={{ fill: "#A7B0C0", fontSize: 10 }}
        />
        <YAxis
          domain={["dataMin - 5", "dataMax + 5"]}
          tickFormatter={formatCurrency}
          tick={{ fill: "#A7B0C0", fontSize: 10 }}
        />
        <Tooltip
          cursor={{ stroke: "rgba(255,255,255,0.2)", strokeWidth: 1 }}
          contentStyle={{ background: "#0F1424", border: "1px solid rgba(255,255,255,0.08)" }}
          formatter={(value: number) => formatCurrency(value)}
          labelFormatter={(label: number) => formatTimestamp(label)}
        />
        <Customized component={Candlesticks} />
        <Line type="monotone" dataKey="ma20" stroke="#7C5CFF" strokeWidth={1.5} dot={false} />
        <Line type="monotone" dataKey="ma50" stroke="#F97316" strokeWidth={1} dot={false} />
        <Brush dataKey="timestamp" height={20} stroke="#7C5CFF" />
      </ComposedChart>
    </ResponsiveContainer>
  );
}

function Candlesticks(props: any) {
  const xAxis = Object.values(props.xAxisMap ?? {})[0];
  const yAxis = Object.values(props.yAxisMap ?? {})[0];
  if (!xAxis || !yAxis) return null;
  const xScale = xAxis.scale;
  const yScale = yAxis.scale;
  const bandwidth = typeof xScale.bandwidth === "function" ? xScale.bandwidth() : 8;
  const candleWidth = Math.max(4, bandwidth * 0.6);

  return (
    <g>
      {props.data.map((d: any) => {
        const x = xScale(d.timestamp) + bandwidth / 2;
        const yOpen = yScale(d.open);
        const yClose = yScale(d.close);
        const yHigh = yScale(d.high);
        const yLow = yScale(d.low);
        const color = d.close >= d.open ? "#10B981" : "#EF4444";
        const rectY = Math.min(yOpen, yClose);
        const rectH = Math.max(1, Math.abs(yOpen - yClose));
        return (
          <g key={d.timestamp}>
            <line x1={x} x2={x} y1={yHigh} y2={yLow} stroke={color} strokeWidth={1} />
            <rect x={x - candleWidth / 2} y={rectY} width={candleWidth} height={rectH} fill={color} />
          </g>
        );
      })}
    </g>
  );
}
