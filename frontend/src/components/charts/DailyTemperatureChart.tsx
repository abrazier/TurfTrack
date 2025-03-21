import React from "react";
import {
  ComposedChart,
  Bar,
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
  temp_max: number;
  temp_min: number;
  temp_mean: number;
  gdd: number;
  cumulative_gdd?: number;
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

    // Filter duplicate temperature values
    const displayEntries = new Map();

    // Process entries to avoid duplicates
    payload.forEach((entry) => {
      const dataKey = entry.dataKey;

      // Skip processing entries without values
      if (entry.value === null || entry.value === undefined) return;

      // Handle temperature metrics to avoid duplicates
      if (dataKey.includes("temp_max")) {
        if (dataKey === "historical_temp_max") {
          displayEntries.set("temp_max", {
            name: "Max Temp",
            value: entry.value,
            color: entry.color,
          });
        } else if (!displayEntries.has("temp_max")) {
          displayEntries.set("temp_max", {
            name: "Max Temp (Forecast)",
            value: entry.value,
            color: entry.color,
          });
        }
      } else if (dataKey.includes("temp_min")) {
        if (dataKey === "historical_temp_min") {
          displayEntries.set("temp_min", {
            name: "Min Temp",
            value: entry.value,
            color: entry.color,
          });
        } else if (!displayEntries.has("temp_min")) {
          displayEntries.set("temp_min", {
            name: "Min Temp (Forecast)",
            value: entry.value,
            color: entry.color,
          });
        }
      } else if (dataKey.includes("temp_mean")) {
        if (dataKey === "historical_temp_mean") {
          displayEntries.set("temp_mean", {
            name: "Mean Temp",
            value: entry.value,
            color: entry.color,
          });
        } else if (!displayEntries.has("temp_mean")) {
          displayEntries.set("temp_mean", {
            name: "Mean Temp (Forecast)",
            value: entry.value,
            color: entry.color,
          });
        }
      } else {
        // For non-temperature metrics (like GDD), show as is
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

// Safe version that avoids TypeScript errors
const findTransitionIndex = (chartData: any[]): number => {
  for (let i = 1; i < chartData.length; i++) {
    const current = chartData[i];
    const previous = chartData[i - 1];

    if (current?.forecast_temp_max && previous?.historical_temp_max) {
      return i;
    }
  }
  return -1;
};

const DailyTemperatureChart: React.FC<Props> = ({ data }) => {
  // Use the helper function instead
  const transitionIndex = findTransitionIndex(data);
  // Add a reference line at the transition point if one was found
  const transitionDate =
    transitionIndex >= 0 ? data[transitionIndex]?.date : null;
  return (
    <ResponsiveContainer width="100%" height={600}>
      <ComposedChart
        data={data}
        margin={{ top: 0, right: 5, left: 5, bottom: 60 }}
      >
        <CartesianGrid strokeDasharray="3 3" stroke="#ccc" />
        <XAxis dataKey="date" tick={<CustomizedAxisTick />} interval={0} />
        {/* Add transition marker if a transition point was found */}
        {transitionDate && (
          <ReferenceLine
            x={transitionDate}
            stroke="#666"
            strokeWidth={2}
            strokeDasharray="5 5"
            label={{ value: "Forecast Start", position: "top", fill: "#666" }}
          />
        )}
        {/* Primary axis for temperatures */}
        <YAxis
          tickFormatter={(value: any) => `${Math.round(value)}°F`}
          domain={([dataMin, dataMax]) => [
            dataMin < 0 ? dataMin : 0,
            dataMax + 5,
          ]}
          label={{
            value: "Temperature (°F)",
            angle: -90,
            position: "insideLeft",
            style: { textAnchor: "middle" },
          }}
        />
        {/* Secondary axis for GDD on the right */}
        <YAxis
          yAxisId="gdd"
          orientation="right"
          domain={[0, (dataMaxGDD: number) => dataMaxGDD + 50]}
        />
        <Tooltip
          content={<CustomTooltip />}
          labelFormatter={(label) => `Date: ${label}`}
        />
        <Legend
          verticalAlign="top"
          align="center"
          wrapperStyle={{ paddingTop: 0 }}
        />
        <Line
          type="monotone"
          dataKey="historical_temp_max"
          stroke="#ff7300"
          name="Max Temp"
          dot={true}
          connectNulls={true}
          // Only show points up to and including the transition point
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="forecast_temp_max"
          stroke="#ff7300"
          name="Forecast Max Temp"
          strokeDasharray="5 5"
          dot={true}
          connectNulls={true}
          // Only show forecast points starting from the transition point
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="historical_temp_min"
          stroke="#387908"
          name="Min Temp"
          dot={true}
          connectNulls={true}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="forecast_temp_min"
          stroke="#387908"
          name="Forecast Min Temp"
          strokeDasharray="5 5"
          dot={true}
          connectNulls={true}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="historical_temp_mean"
          stroke="#0000ff"
          name="Mean Temp"
          dot={true}
          connectNulls={true}
          isAnimationActive={false}
        />
        <Line
          type="monotone"
          dataKey="forecast_temp_mean"
          stroke="#0000ff"
          name="Forecast Mean Temp"
          strokeDasharray="5 5"
          dot={true}
          connectNulls={true}
          isAnimationActive={false}
        />
        <Bar
          dataKey="cumulative_gdd"
          fill="#ff00ff"
          name="Cumulative GDD"
          yAxisId="gdd"
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
};

export default DailyTemperatureChart;
