import React from "react";
import {
  ResponsiveContainer,
  ComposedChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ReferenceLine,
} from "recharts";

interface Props {
  data: any[];
}

interface PayloadEntry {
  dataKey: string;
  value: number | null;
  name: string;
  color: string;
}

const CustomTooltip: React.FC<any> = ({ active, payload, label }) => {
  if (active && payload && payload.length) {
    const formattedLabel = label ? `Date: ${label}` : "Date: N/A";

    // Filter duplicate values similar to TemperatureChart tooltip
    const displayEntries = new Map();

    // Process entries to avoid duplicates
    payload.forEach((entry: PayloadEntry) => {
      const dataKey = entry.dataKey;

      if (entry.value === null || entry.value === undefined) return;

      if (dataKey === "dollar_spot_probability") {
        displayEntries.set("dollar_spot", {
          name: "Dollar Spot Risk",
          value: (entry.value * 100).toFixed(1) + "%",
          color: entry.color,
        });
      } else if (
        dataKey === "forecast_dollar_spot_probability" &&
        !displayEntries.has("dollar_spot")
      ) {
        displayEntries.set("dollar_spot", {
          name: "Dollar Spot Risk (Forecast)",
          value: (entry.value * 100).toFixed(1) + "%",
          color: entry.color,
        });
      } else {
        displayEntries.set(dataKey, {
          name: entry.name,
          value: entry.value,
          color: entry.color,
        });
      }
    });

    const entries = Array.from(displayEntries.values());

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
        {entries.map((entry, index) => (
          <p
            key={`item-${index}`}
            style={{ color: entry.color || "#000", margin: 0 }}
          >
            {`${entry.name}: ${entry.value}`}
          </p>
        ))}
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

const DollarSpotChart: React.FC<Props> = ({ data }) => {
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
        <Tooltip content={<CustomTooltip />} />
        <Legend
          verticalAlign="top"
          align="center"
          wrapperStyle={{ paddingTop: 0 }}
        />
        <ReferenceLine
          y={0.7}
          label="High Risk"
          stroke="red"
          strokeDasharray="3 3"
        />
        <ReferenceLine
          y={0.3}
          label="Moderate Risk"
          stroke="orange"
          strokeDasharray="3 3"
        />
        <Line
          type="monotone"
          dataKey="dollar_spot_probability"
          stroke="#8884d8"
          name="Dollar Spot Risk"
          dot={false}
          connectNulls={true}
        />
        <Line
          type="monotone"
          dataKey="forecast_dollar_spot_probability"
          stroke="#8884d8"
          strokeDasharray="5 5"
          name="Dollar Spot Risk (Forecast)"
          dot={false}
          connectNulls={true}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default DollarSpotChart;
