import React from "react";
import {
  ComposedChart,
  Line,
  CartesianGrid,
  XAxis,
  YAxis,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
} from "recharts";

interface DailyData {
  date: string;
  growth_potential: number;
}

interface Props {
  data: DailyData[];
}

interface CustomTooltipProps {
  active?: boolean;
  payload?: any[];
  label?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({
  active,
  payload,
  label,
}) => {
  if (active && payload && payload.length) {
    const formattedLabel = label ? `Date: ${label}` : "Date: N/A";
    return (
      <div
        style={{
          backgroundColor: "white",
          border: "1px solid #ccc",
          padding: "5px",
          color: "#000",
        }}
      >
        <p style={{ margin: 0, color: "#000" }}>{formattedLabel}</p>
        {payload.map((entry, index) => {
          // Check if the current entry represents growth potential:
          const isGrowthPotential =
            entry.dataKey === "growth_potential" ||
            entry.name === "Growth Potential";
          const valueFormatted = isGrowthPotential
            ? `${(entry.value * 100).toFixed(0)}%`
            : entry.value;
          return (
            <p
              key={`tooltip-${index}`}
              style={{ color: entry.color || "#000", margin: 0 }}
            >
              {`${entry.name}: ${valueFormatted}`}
            </p>
          );
        })}
      </div>
    );
  }
  return null;
};

const CustomizedAxisTick: React.FC<any> = ({ x, y, payload }) => {
  return (
    <g transform={`translate(${x},${y})`}>
      <text
        x={0}
        y={0}
        dy={16}
        textAnchor="end"
        fill="#666"
        transform="rotate(-45)"
      >
        {payload.value}
      </text>
    </g>
  );
};

const DailyGrowthPotentialChart: React.FC<Props> = ({ data }) => {
  return (
    <ResponsiveContainer width="100%" height={400}>
      <ComposedChart
        data={data}
        margin={{ top: 0, right: 15, left: 5, bottom: 60 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#ccc" />
        <XAxis dataKey="date" tick={<CustomizedAxisTick />} interval={0} />
        <YAxis
          tickFormatter={(value) => `${(value * 100).toFixed(0)}%`}
          domain={[0, 1]}
        />
        <Tooltip
          content={<CustomTooltip />}
          labelFormatter={(label) => `Date: ${label}`}
        />
        {/* Place the legend at the bottom and add some wrapper styling */}
        <Legend
          verticalAlign="top"
          align="center"
          wrapperStyle={{ paddingTop: 0 }}
        />
        <ReferenceLine
          y={0.7}
          isFront={true}
          label="Optimum Growth Potential"
          stroke="green"
          strokeDasharray="3 3"
        />
        <Line
          type="monotone"
          dataKey="growth_potential"
          stroke="#ff7300"
          name="Historical Growth Potential"
          dot={false}
        />
        <Line
          type="monotone"
          dataKey="forecast_growth_potential"
          stroke="#ff7300"
          name="Forecast Growth Potential"
          strokeDasharray="3 3"
          dot={false}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default DailyGrowthPotentialChart;
