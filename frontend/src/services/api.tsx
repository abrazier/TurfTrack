import { WeatherDataItem } from "../types/weather";

export async function getDailyWeather(): Promise<WeatherDataItem[]> {
  const response = await fetch("/api/daily");
  if (!response.ok) {
    throw new Error("Failed to fetch daily weather data");
  }
  return response.json();
}

export async function getForecastData(): Promise<WeatherDataItem[]> {
  const response = await fetch("/api/daily-forecast");
  if (!response.ok) {
    throw new Error("Failed to fetch forecast data");
  }
  return response.json();
}
