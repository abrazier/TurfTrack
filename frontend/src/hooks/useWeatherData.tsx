import { useState, useEffect } from "react";
import { getDailyWeather, getForecastData } from "../services/api";
import { WeatherDataItem } from "../types/weather";
import { celsiusToFahrenheit } from "../utils/conversions";

// Simple named export function to ensure Fast Refresh works
export function useWeatherData() {
  const [dailyData, setDailyData] = useState<WeatherDataItem[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<Error | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        setLoading(true);
        const historicalData = await getDailyWeather();
        const forecastData = await getForecastData();

        // Process historical data
        const convertedHistoricalData = historicalData.map((item) => {
          const convertedMax =
            item.temp_max !== null
              ? Number(celsiusToFahrenheit(item.temp_max).toFixed(2))
              : null;
          const convertedMin =
            item.temp_min !== null
              ? Number(celsiusToFahrenheit(item.temp_min).toFixed(2))
              : null;
          const temp_mean =
            convertedMax !== null && convertedMin !== null
              ? Number(((convertedMax + convertedMin) / 2).toFixed(2))
              : null;

          return {
            ...item,
            temp_mean: temp_mean,
            gdd: item.forecast_gdd || 0,
            growth_potential: item.growth_potential || 0,
            historical_temp_max: convertedMax,
            historical_temp_min: convertedMin,
            historical_temp_mean: temp_mean,
            dollar_spot_probability: item.dollar_spot_probability,
            forecast_temp_max: null,
            forecast_temp_min: null,
            forecast_temp_mean: null,
            forecast_growth_potential: null,
            forecast_dollar_spot_probability: null,
            isForecast: false,
          };
        });

        // Get the last cumulative GDD from historical data
        let lastCumulativeGDD = convertedHistoricalData.length
          ? convertedHistoricalData[convertedHistoricalData.length - 1]
              .cumulative_gdd
          : 0;

        // Process forecast data
        const convertedForecastData = forecastData.map((item) => {
          const convertedMax =
            item.temp_max !== null
              ? Number(celsiusToFahrenheit(item.temp_max).toFixed(2))
              : null;
          const convertedMin =
            item.temp_min !== null
              ? Number(celsiusToFahrenheit(item.temp_min).toFixed(2))
              : null;
          const temp_mean =
            convertedMax !== null && convertedMin !== null
              ? Number(((convertedMax + convertedMin) / 2).toFixed(2))
              : null;

          const forecastDailyGDD = item.forecast_gdd || 0;
          lastCumulativeGDD += forecastDailyGDD;

          return {
            ...item,
            temp_mean: temp_mean,
            gdd: forecastDailyGDD,
            growth_potential: item.growth_potential || 0,
            historical_temp_max: null,
            historical_temp_min: null,
            historical_temp_mean: null,
            dollar_spot_probability: null,
            forecast_dollar_spot_probability: item.dollar_spot_probability,
            forecast_temp_max: convertedMax,
            forecast_temp_min: convertedMin,
            forecast_temp_mean: temp_mean,
            cumulative_gdd: lastCumulativeGDD,
            isForecast: true,
          };
        });

        // Simply merge and sort the data - no bridging needed
        const mergedData = [
          ...convertedHistoricalData,
          ...convertedForecastData,
        ].sort(
          (a, b) => new Date(a.date).getTime() - new Date(b.date).getTime()
        );

        setDailyData(mergedData);
      } catch (error) {
        console.error("Data fetch error", error);
        setError(error as Error);
      } finally {
        setLoading(false);
      }
    }

    fetchData();
  }, []);

  return { dailyData, loading, error };
}
