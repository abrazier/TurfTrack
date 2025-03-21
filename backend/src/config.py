from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    DEBUG: bool
    DATABASE_URL: str
    OPENWEATHER_API_KEY: Optional[str] = None
    DEFAULT_LATITUDE: float
    DEFAULT_LONGITUDE: float
    LOCAL_TIMEZONE: str

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
