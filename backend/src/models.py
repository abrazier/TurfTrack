import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class WeatherData(Base):
    __tablename__ = "weather_data"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    city_name = Column(String, nullable=False)
    temperature = Column(Float, nullable=False)
    feels_like = Column(Float, nullable=False)
    temp_min = Column(Float)
    temp_max = Column(Float)
    pressure = Column(Integer)
    humidity = Column(Integer)
    sea_level = Column(Integer)
    grnd_level = Column(Integer)
    wind_speed = Column(Float)
    wind_deg = Column(Integer)
    wind_gust = Column(Float)
    description = Column(String, nullable=False)
    recorded_at = Column(DateTime, default=datetime.datetime.utcnow)
