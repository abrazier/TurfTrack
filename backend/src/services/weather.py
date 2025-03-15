import os
import abc
import requests
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env


class WeatherProvider(abc.ABC):
    @abc.abstractmethod
    def get_weather(self, **kwargs) -> dict:
        """Retrieve weather data based on provided parameters."""
        pass


class OpenWeatherMapProvider(WeatherProvider):
    def __init__(self, api_key: str = None):
        # Use the API key from the .env file
        self.api_key = api_key or os.getenv("OPENWEATHER_API_KEY")
        if not self.api_key:
            raise ValueError("OpenWeatherMap API key not provided")
        self.url = "https://api.openweathermap.org/data/2.5/weather"

    def get_weather(
        self, lat: float = 41.8781, lon: float = -87.6298, units: str = "metric"
    ) -> dict:
        """
        Retrieve current weather data using latitude and longitude.
        Defaults to Chicago's coordinates.
        """
        params = {"lat": lat, "lon": lon, "appid": self.api_key, "units": units}
        response = requests.get(self.url, params=params)
        response.raise_for_status()
        return response.json()
