from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.services.weather import OpenMeteoProvider
from src.database import engine, SessionLocal
from src.models import Base, DailyWeatherData, HourlyWeatherData
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from fastapi.responses import JSONResponse
from src.utils import read_last_fetch_time, write_last_fetch_time
from datetime import timezone


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()


def fetch_daily_weather(
    start_date,
    end_date,
    provider="openmeteo",
    lat=settings.DEFAULT_LATITUDE,
    lon=settings.DEFAULT_LONGITUDE,
):
    session = SessionLocal()
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    if provider.lower() == "openmeteo":
        weather_provider = OpenMeteoProvider()
        weather = weather_provider.get_daily_weather(
            lat=lat,
            lon=lon,
            start_date=start_date_str,
            end_date=end_date_str,
            timezone="auto",
        )
    else:
        pass

    daily_times = weather.get("daily", {}).get("time", [])
    for i, date_str in enumerate(daily_times):
        date = datetime.strptime(date_str, "%Y-%m-%d").date()  # Convert to date object
        daily_weather = DailyWeatherData(
            city_name=weather.get("timezone", "Unknown"),
            date=date,  # Add this line
            temp_max=weather.get("daily", {}).get("temperature_2m_max", [None])[i],
            temp_min=weather.get("daily", {}).get("temperature_2m_min", [None])[i],
            rain_sum=weather.get("daily", {}).get("rain_sum", [None])[i],
            sunshine_duration=weather.get("daily", {}).get("sunshine_duration", [None])[
                i
            ],
            precip_prob_max=weather.get("daily", {}).get(
                "precipitation_probability_max", [None]
            )[i],
            uv_index_max=weather.get("daily", {}).get("uv_index_max", [None])[i],
            et0_fao_evapotranspiration=weather.get("daily", {}).get(
                "et0_fao_evapotranspiration", [None]
            )[i],
            precipitation_sum=weather.get("daily", {}).get("precipitation_sum", [None])[
                i
            ],
            precipitation_hours=weather.get("daily", {}).get(
                "precipitation_hours", [None]
            )[i],
            wind_direction_10m_dominant=weather.get("daily", {}).get(
                "wind_direction_10m_dominant", [None]
            )[i],
            snowfall_sum=weather.get("daily", {}).get("snowfall_sum", [None])[i],
            extra_data=weather,
        )
        session.add(daily_weather)
    session.commit()
    session.close()


def fetch_hourly_weather(
    start_date,
    end_date,
    provider="openmeteo",
    lat=settings.DEFAULT_LATITUDE,
    lon=settings.DEFAULT_LONGITUDE,
):
    session = SessionLocal()
    start_date_str = start_date.strftime("%Y-%m-%d")
    end_date_str = end_date.strftime("%Y-%m-%d")
    if provider.lower() == "openmeteo":
        weather_provider = OpenMeteoProvider()
        weather = weather_provider.get_hourly_weather(
            lat=lat,
            lon=lon,
            start_date=start_date_str,
            end_date=end_date_str,
            timezone="auto",
        )
    else:
        pass

    hourly_times = weather.get("hourly", {}).get("time", [])
    for i, time_str in enumerate(hourly_times):
        date = datetime.fromisoformat(time_str)  # Convert to datetime object
        hourly_weather = HourlyWeatherData(
            city_name=weather.get("timezone", "Unknown"),
            date=date,  # Add this line
            temperature=weather.get("hourly", {}).get("temperature_2m", [None])[i],
            soil_temperature_0cm=weather.get("hourly", {}).get(
                "soil_temperature_0cm", [None]
            )[i],
            soil_temperature_6cm=weather.get("hourly", {}).get(
                "soil_temperature_6cm", [None]
            )[i],
            soil_temperature_18cm=weather.get("hourly", {}).get(
                "soil_temperature_18cm", [None]
            )[i],
            soil_temperature_54cm=weather.get("hourly", {}).get(
                "soil_temperature_54cm", [None]
            )[i],
            soil_moisture_0_to_1cm=weather.get("hourly", {}).get(
                "soil_moisture_0_to_1cm", [None]
            )[i],
            soil_moisture_1_to_3cm=weather.get("hourly", {}).get(
                "soil_moisture_1_to_3cm", [None]
            )[i],
            soil_moisture_3_to_9cm=weather.get("hourly", {}).get(
                "soil_moisture_3_to_9cm", [None]
            )[i],
            soil_moisture_9_to_27cm=weather.get("hourly", {}).get(
                "soil_moisture_9_to_27cm", [None]
            )[i],
            soil_moisture_27_to_81cm=weather.get("hourly", {}).get(
                "soil_moisture_27_to_81cm", [None]
            )[i],
            relative_humidity_2m=weather.get("hourly", {}).get(
                "relative_humidity_2m", [None]
            )[i],
            dew_point_2m=weather.get("hourly", {}).get("dew_point_2m", [None])[i],
            precipitation_probability=weather.get("hourly", {}).get(
                "precipitation_probability", [None]
            )[i],
            precipitation=weather.get("hourly", {}).get("precipitation", [None])[i],
            rain=weather.get("hourly", {}).get("rain", [None])[i],
            showers=weather.get("hourly", {}).get("showers", [None])[i],
            snowfall=weather.get("hourly", {}).get("snowfall", [None])[i],
            snow_depth=weather.get("hourly", {}).get("snow_depth", [None])[i],
            apparent_temperature=weather.get("hourly", {}).get(
                "apparent_temperature", [None]
            )[i],
            evapotranspiration=weather.get("hourly", {}).get(
                "evapotranspiration", [None]
            )[i],
            et0_fao_evapotranspiration=weather.get("hourly", {}).get(
                "et0_fao_evapotranspiration", [None]
            )[i],
            extra_data=weather,
        )
        session.add(hourly_weather)
    session.commit()
    session.close()


def fetch_weather_data(start_date, end_date):
    for single_date in (
        start_date + timedelta(n) for n in range((end_date - start_date).days + 1)
    ):
        fetch_daily_weather(single_date, single_date)
        fetch_hourly_weather(single_date, single_date)


def fetch_initial_data():
    end_date = datetime.utcnow() - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    fetch_weather_data(start_date, end_date)


def schedule_daily_fetch():
    def daily_fetch_wrapper():
        logger.info("Executing daily fetch task")
        last_fetch_time = read_last_fetch_time()
        if last_fetch_time:
            start_date = last_fetch_time
        else:
            start_date = datetime.utcnow() - timedelta(days=1)
        end_date = datetime.utcnow() - timedelta(days=1)
        fetch_daily_weather(start_date, end_date)
        write_last_fetch_time(end_date)

    scheduler.add_job(daily_fetch_wrapper, "cron", hour=1, minute=0)
    if not scheduler.running:
        scheduler.start()
        logger.info("Daily fetch scheduler started")


def schedule_hourly_fetch():
    def hourly_fetch_wrapper():
        logger.info("Executing hourly fetch task")
        last_fetch_time = read_last_fetch_time()
        if last_fetch_time:
            start_date = last_fetch_time
        else:
            start_date = datetime.utcnow() - timedelta(hours=4)
        end_date = datetime.utcnow() - timedelta(hours=4)
        fetch_hourly_weather(start_date, end_date)
        write_last_fetch_time(end_date)

    scheduler.add_job(hourly_fetch_wrapper, "cron", hour="*/4", minute=0)
    if not scheduler.running:
        scheduler.start()
        logger.info("Hourly fetch scheduler started")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    if not session.query(DailyWeatherData).first():
        fetch_initial_data()
        write_last_fetch_time(datetime.utcnow() - timedelta(days=1))
    session.close()
    schedule_daily_fetch()
    schedule_hourly_fetch()


@app.get("/")
async def get_main():
    return "Hello, World!"


@app.get("/api/scheduler/status")
async def get_scheduler_status():
    jobs = scheduler.get_jobs()
    job_details = [
        {
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat()
            if job.next_run_time
            else None,
        }
        for job in jobs
    ]
    return JSONResponse(content={"jobs": job_details})


@app.post("/api/fetch")
async def manual_fetch():
    fetch_weather_data(
        datetime.now(timezone.utc) - timedelta(days=1),
        datetime.now(timezone.utc),
    )
    return {"message": "Data fetched successfully"}


@app.get("/api/daily")
async def get_daily_data():
    session = SessionLocal()
    data = session.query(DailyWeatherData).all()
    session.close()
    return data


@app.get("/api/hourly")
async def get_hourly_data():
    session = SessionLocal()
    data = session.query(HourlyWeatherData).all()
    session.close()
    return data
