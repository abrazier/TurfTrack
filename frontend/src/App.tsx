import { useWeatherData } from "./hooks/useWeatherData";
import DailyTemperatureChart from "./components/charts/DailyTemperatureChart";
import GrowthPotentialChart from "./components/charts/GrowthPotentialChart";
import DollarSpotChart from "./components/charts/DollarSpotChart";

// Define what DailyData looks like based on chart requirements
interface DailyData {
  date: string;
  temp_max: number;
  temp_min: number;
  temp_mean: number;
  gdd: number;
  historical_temp_max: number;
  historical_temp_min: number;
  historical_temp_mean: number;
  forecast_temp_max: number;
  forecast_temp_min: number;
  forecast_temp_mean: number;
  cumulative_gdd: number;
  growth_potential: number;
  forecast_growth_potential: number;
  dollar_spot_probability: number;
  forecast_dollar_spot_probability: number;
  isForecast: boolean;
}

function App() {
  const { dailyData, loading, error } = useWeatherData();

  // Simplified data transformation - just replace nulls with zeros
  const adaptedData: DailyData[] = dailyData.map((item) => ({
    date: item.date,
    temp_max: item.temp_max ?? 0,
    temp_min: item.temp_min ?? 0,
    temp_mean: item.temp_mean ?? 0,
    gdd: item.gdd || 0,
    historical_temp_max: item.historical_temp_max ?? 0,
    historical_temp_min: item.historical_temp_min ?? 0,
    historical_temp_mean: item.historical_temp_mean ?? 0,
    forecast_temp_max: item.forecast_temp_max ?? 0,
    forecast_temp_min: item.forecast_temp_min ?? 0,
    forecast_temp_mean: item.forecast_temp_mean ?? 0,
    cumulative_gdd: item.cumulative_gdd ?? 0,
    growth_potential: item.growth_potential ?? 0,
    forecast_growth_potential: item.forecast_growth_potential ?? 0,
    dollar_spot_probability: item.dollar_spot_probability ?? 0,
    forecast_dollar_spot_probability:
      item.forecast_dollar_spot_probability ?? 0,
    isForecast: item.isForecast ?? false,
  }));

  if (loading) {
    return <p>Loading...</p>;
  }

  if (error) {
    return <p>Error: {error.message}</p>;
  }

  // Rest of your component remains the same
  return (
    <div style={{ width: "100%", padding: "20px", boxSizing: "border-box" }}>
      <h1>Welcome to TurfTrack</h1>
      {adaptedData.length ? (
        <div>
          {/* Temperature chart at full width */}
          <div style={{ width: "100%", height: "600px", marginBottom: "20px" }}>
            <DailyTemperatureChart data={adaptedData} />
          </div>

          {/* Flexbox container for the two smaller charts */}
          <div
            style={{
              display: "flex",
              flexDirection: "row",
              flexWrap: "wrap",
              gap: "20px",
              justifyContent: "space-between",
            }}
          >
            {/* Growth Potential Chart */}
            <div
              style={{
                flex: "1 1 45%",
                minWidth: "400px",
                height: "400px",
              }}
            >
              <GrowthPotentialChart data={adaptedData} />
            </div>

            {/* Dollar Spot Chart */}
            <div
              style={{
                flex: "1 1 45%",
                minWidth: "400px",
                height: "400px",
              }}
            >
              <DollarSpotChart data={adaptedData} />
            </div>
          </div>
        </div>
      ) : (
        <p>No data available</p>
      )}
    </div>
  );
}

export default App;
