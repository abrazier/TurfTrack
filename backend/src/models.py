from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Date
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class DailyWeatherData(Base):
    __tablename__ = "daily_weather_data"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(Date, index=True)
    temp_max = Column(Float, nullable=True)
    temp_min = Column(Float, nullable=True)
    rain_sum = Column(Float, nullable=True)
    sunshine_duration = Column(Float, nullable=True)
    precip_prob_max = Column(Float, nullable=True)
    uv_index_max = Column(Float, nullable=True)
    et0_fao_evapotranspiration = Column(Float, nullable=True)
    precipitation_sum = Column(Float, nullable=True)
    precipitation_hours = Column(Float, nullable=True)
    wind_direction_10m_dominant = Column(Float, nullable=True)
    snowfall_sum = Column(Float, nullable=True)
    gdd = Column(Float, default=0.0, nullable=True)
    cumulative_gdd = Column(Float, default=0.0, nullable=True)
    growth_potential = Column(Float, default=0.0, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    dollar_spot_probability = Column(Float, default=0.0, nullable=True)


class DailyForecastWeatherData(Base):
    __tablename__ = "daily_forecast_weather_data"
    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, unique=True, index=True, nullable=False)
    temp_max = Column(Float, nullable=True)
    temp_min = Column(Float, nullable=True)
    rain_sum = Column(Float, nullable=True)
    sunshine_duration = Column(Float, nullable=True)
    precip_prob_max = Column(Float, nullable=True)
    uv_index_max = Column(Float, nullable=True)
    et0_fao_evapotranspiration = Column(Float, nullable=True)
    precipitation_sum = Column(Float, nullable=True)
    precipitation_hours = Column(Float, nullable=True)
    wind_direction_10m_dominant = Column(Float, nullable=True)
    snowfall_sum = Column(Float, nullable=True)
    forecast_gdd = Column(Float, nullable=True)
    forecast_growth_potential = Column(Float, nullable=True)
    forecast_dollar_spot_probability = Column(Float, default=0.0, nullable=True)


class HourlyWeatherData(Base):
    __tablename__ = "hourly_weather_data"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    date = Column(DateTime, index=True)
    temperature = Column(Float, nullable=True)
    soil_temperature_0cm = Column(Float, nullable=True)
    soil_temperature_6cm = Column(Float, nullable=True)
    soil_temperature_18cm = Column(Float, nullable=True)
    soil_temperature_54cm = Column(Float, nullable=True)
    soil_moisture_0_to_1cm = Column(Float, nullable=True)
    soil_moisture_1_to_3cm = Column(Float, nullable=True)
    soil_moisture_3_to_9cm = Column(Float, nullable=True)
    soil_moisture_9_to_27cm = Column(Float, nullable=True)
    soil_moisture_27_to_81cm = Column(Float, nullable=True)
    relative_humidity_2m = Column(Float, nullable=True)
    dew_point_2m = Column(Float, nullable=True)
    precipitation_probability = Column(Float, nullable=True)
    precipitation = Column(Float, nullable=True)
    rain = Column(Float, nullable=True)
    showers = Column(Float, nullable=True)
    snowfall = Column(Float, nullable=True)
    snow_depth = Column(Float, nullable=True)
    apparent_temperature = Column(Float, nullable=True)
    evapotranspiration = Column(Float, nullable=True)
    et0_fao_evapotranspiration = Column(Float, nullable=True)
    recorded_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
