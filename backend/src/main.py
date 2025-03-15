from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from src.config import Config
from src.services.weather import OpenWeatherMapProvider
from src.database import engine, SessionLocal
from src.models import Base, WeatherData

app = FastAPI(debug=Config.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Create database tables on startup
@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
async def get_main():
    return "Hello, World!"


@app.get("/api/weather")
async def get_weather():
    try:
        provider = OpenWeatherMapProvider()
        weather = provider.get_weather()  # Defaults to Chicago's weather
        # Open database session
        session = SessionLocal()
        # Extract data from API response
        main_data = weather.get("main", {})
        wind_data = weather.get("wind", {})
        weather_entry = WeatherData(
            city_name=weather.get("name", "Unknown"),
            temperature=main_data.get("temp"),
            feels_like=main_data.get("feels_like"),
            temp_min=main_data.get("temp_min"),
            temp_max=main_data.get("temp_max"),
            pressure=main_data.get("pressure"),
            humidity=main_data.get("humidity"),
            sea_level=main_data.get("sea_level"),
            grnd_level=main_data.get("grnd_level"),
            wind_speed=wind_data.get("speed"),
            wind_deg=wind_data.get("deg"),
            wind_gust=wind_data.get("gust"),
            description=weather.get("weather", [{}])[0].get(
                "description", "No description"
            ),
        )
        session.add(weather_entry)
        session.commit()
        session.refresh(weather_entry)
        session.close()
        return weather
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
