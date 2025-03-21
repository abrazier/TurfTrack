export interface WeatherDataItem {
  date: string;
  temp_min: number | null;
  temp_max: number | null;
  temp_mean: number | null; // Add this
  gdd: number; // Add this
  forecast_gdd?: number;
  historical_temp_max: number | null;
  historical_temp_min: number | null;
  historical_temp_mean: number | null;
  dollar_spot_probability: number | null | undefined;
  forecast_dollar_spot_probability: number | null | undefined;
  forecast_temp_max: number | null;
  forecast_temp_min: number | null;
  forecast_temp_mean: number | null;
  cumulative_gdd: number;
  growth_potential: number;
  forecast_growth_potential: number | null | undefined;
  isForecast?: boolean;
}

export interface ChartProps {
  data: WeatherDataItem[];
}

export interface PayloadEntry {
  dataKey: string;
  value: number | null;
  name: string;
  color: string;
}
