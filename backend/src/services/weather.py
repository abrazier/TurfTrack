import os
import abc
import requests
import requests_cache
from retry_requests import retry
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


class WeatherProvider(abc.ABC):
    @abc.abstractmethod
    def get_daily_weather(self, **kwargs) -> dict:
        """Retrieve weather data based on provided parameters."""
        pass

    @abc.abstractmethod
    def get_hourly_weather(self, **kwargs) -> dict:
        """Retrieve weather data based on provided parameters."""
        pass


class OpenMeteoProvider(WeatherProvider):
    def __init__(self):
        cache_session = requests_cache.CachedSession(".cache", expire_after=3600)
        self.session = retry(cache_session, retries=5, backoff_factor=0.2)
        self.url = "https://api.open-meteo.com/v1/forecast"

    def get_daily_weather(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        timezone: str = "auto",
        daily: list = None,
    ) -> dict:
        if daily is None:
            daily = [
                "temperature_2m_max",
                "temperature_2m_min",
                "rain_sum",
                "sunshine_duration",
                "precipitation_probability_max",
                "uv_index_max",
                "et0_fao_evapotranspiration",
                "precipitation_sum",
                "precipitation_hours",
                "wind_direction_10m_dominant",
                "snowfall_sum",
            ]
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
            "start_date": start_date,
            "end_date": end_date,
            "daily": ",".join(daily),
        }
        response = self.session.get(self.url, params=params)
        response.raise_for_status()
        return response.json()

    def get_hourly_weather(
        self,
        lat: float,
        lon: float,
        start_date: str,
        end_date: str,
        timezone: str = "auto",
        hourly: list = None,
    ) -> dict:
        if hourly is None:
            hourly = [
                "temperature_2m",
                "soil_temperature_0cm",
                "soil_temperature_6cm",
                "soil_temperature_18cm",
                "soil_temperature_54cm",
                "soil_moisture_0_to_1cm",
                "soil_moisture_1_to_3cm",
                "soil_moisture_3_to_9cm",
                "soil_moisture_9_to_27cm",
                "soil_moisture_27_to_81cm",
                "relative_humidity_2m",
                "dew_point_2m",
                "precipitation_probability",
                "precipitation",
                "rain",
                "showers",
                "snowfall",
                "snow_depth",
                "apparent_temperature",
                "evapotranspiration",
                "et0_fao_evapotranspiration",
            ]
        params = {
            "latitude": lat,
            "longitude": lon,
            "timezone": timezone,
            "start_date": start_date,
            "end_date": end_date,
            "hourly": ",".join(hourly),
        }
        response = self.session.get(self.url, params=params)
        response.raise_for_status()
        return response.json()
