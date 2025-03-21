from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.config import settings
from src.services.weather import OpenMeteoProvider
from src.database import engine, SessionLocal
from src.models import (
    Base,
    DailyWeatherData,
    DailyForecastWeatherData,
)
from datetime import datetime, timedelta
from apscheduler.schedulers.background import BackgroundScheduler
import logging
from fastapi.responses import JSONResponse
from src.utils import read_last_fetch_time, write_last_fetch_time
from datetime import timezone
import math
import numpy as np
from zoneinfo import ZoneInfo

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(debug=settings.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # React dev server URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

scheduler = BackgroundScheduler()


def growingDegreeDays(avg_temp: float) -> float:
    """
    Calculate the growing degree days (GDD) for a given average temperature.
    The baseline threshold is 10°C -- temperatures below that do not contribute to GDD.

    Parameters:
        avg_temp (float): The average temperature in Celsius.

    Returns:
        float: The GDD, which is max(avg_temp - 10, 0)
    """
    threshold = 10.0
    return max(avg_temp - threshold, 0)


def growthPotential(avg_temp: float) -> float:
    """
    Calculate the growth potential for a given average temperature.
    The formula is: exp(-0.5 * (((avg_temp - 20)/5.5) ** 2))

    Parameters:
        avg_temp (float): The average temperature in Celsius.

    Returns:
        float: The growth potential.
    """
    return math.exp(-0.5 * (((avg_temp - 20) / 5.5) ** 2))


def dollarSpotProbability(avg_temp: float, rel_humidity: float) -> float:
    """
    Calculate the probability of dollar spot disease development using the Smith-Kerns model.

    The model uses a logistic regression equation:
    P(DS) = exp(b₀ + b₁×T + b₂×RH) / (1 + exp(b₀ + b₁×T + b₂×RH))

    Parameters:
        avg_temp (float): Average air temperature in Celsius
        rel_humidity (float): Relative humidity (%)

    Returns:
        float: Probability of dollar spot development (0-1)
    """
    # Model coefficients
    b0 = -8.37
    b1 = 0.15
    b2 = 0.06

    # Calculate the exponent
    exponent = b0 + (b1 * avg_temp) + (b2 * rel_humidity)

    # Apply logistic function
    probability = math.exp(exponent) / (1 + math.exp(exponent))

    # Ensure result is between 0 and 1 and round to 2 decimal places
    return round(max(0.0, min(1.0, probability)), 2)


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
            timezone=settings.LOCAL_TIMEZONE,  # Return dates using our local timezone
        )
        if isinstance(weather, list):
            weather = weather[0]
    else:
        raise NotImplementedError("Only 'openmeteo' is supported at the moment.")

    # Use the new interface from the openmeteo package
    daily = weather.Daily()
    # Log key time attributes returned by the API (if available)
    raw_time = daily.Time()

    # Retrieve the variables (order must match your API call)
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(2).ValuesAsNumpy()
    daily_sunshine_duration = daily.Variables(3).ValuesAsNumpy()
    daily_precip_prob_max = daily.Variables(4).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(5).ValuesAsNumpy()
    daily_et0 = daily.Variables(6).ValuesAsNumpy()
    daily_precip_sum = daily.Variables(7).ValuesAsNumpy()
    daily_precip_hours = daily.Variables(8).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(9).ValuesAsNumpy()
    daily_snowfall_sum = daily.Variables(10).ValuesAsNumpy()

    # Get hourly data for relative humidity
    hourly = weather.Hourly()

    # Fix for 'int' object is not iterable error
    hourly_start_ts = hourly.Time()  # Start timestamp
    hourly_end_ts = hourly.TimeEnd()  # End timestamp
    hourly_interval = hourly.Interval()  # Interval between timestamps

    # Create a list of timestamps using range
    hourly_times = list(range(hourly_start_ts, hourly_end_ts, hourly_interval))

    hourly_humidity = hourly.Variables(
        0
    ).ValuesAsNumpy()  # First (and only) hourly variable

    # Group hourly humidity by day
    daily_humidity_avg = {}
    for i, ts in enumerate(hourly_times):
        if i < len(hourly_humidity) and hourly_humidity[i] is not None:
            utc_date = datetime.fromtimestamp(ts, tz=timezone.utc)
            date_key = utc_date.astimezone(ZoneInfo(settings.LOCAL_TIMEZONE)).date()

            if date_key not in daily_humidity_avg:
                daily_humidity_avg[date_key] = {"sum": 0, "count": 0}

            daily_humidity_avg[date_key]["sum"] += hourly_humidity[i]
            daily_humidity_avg[date_key]["count"] += 1

    # Calculate averages
    for date_key in daily_humidity_avg:
        if daily_humidity_avg[date_key]["count"] > 0:
            daily_humidity_avg[date_key] = (
                daily_humidity_avg[date_key]["sum"]
                / daily_humidity_avg[date_key]["count"]
            )
        else:
            daily_humidity_avg[date_key] = None

    # Then proceed as before:
    daily_times = raw_time
    if not isinstance(daily_times, (list, tuple)):
        daily_times = [daily_times]

    for i, ts in enumerate(daily_times):
        # Current conversion – assuming ts is UTC
        utc_date = datetime.fromtimestamp(ts, tz=timezone.utc)
        converted_local_date = utc_date.astimezone(
            ZoneInfo(settings.LOCAL_TIMEZONE)
        ).date()

        # Get daily average humidity for this date
        avg_humidity = daily_humidity_avg.get(converted_local_date, None)

        max_temp = daily_temperature_2m_max[i]
        min_temp = daily_temperature_2m_min[i]
        max_temp = float(max_temp) if max_temp is not None else None
        min_temp = float(min_temp) if min_temp is not None else None

        daily_gdd = None
        growth_potential = None
        if max_temp is not None and min_temp is not None:
            avg_temp = (max_temp + min_temp) / 2
            daily_gdd = float(round(growingDegreeDays(avg_temp), 2))
            growth_potential = float(round(growthPotential(avg_temp), 2))
        prev_record = (
            session.query(DailyWeatherData)
            .order_by(DailyWeatherData.date.desc())
            .first()
        )
        prev_cumulative = (
            prev_record.cumulative_gdd
            if prev_record and prev_record.cumulative_gdd is not None
            else 0.0
        )
        cumulative_gdd = (
            daily_gdd + prev_cumulative if daily_gdd is not None else prev_cumulative
        )

        # Calculate dollar spot probability
        dollar_spot_prob = None
        if max_temp is not None and min_temp is not None and avg_humidity is not None:
            avg_temp = (max_temp + min_temp) / 2
            dollar_spot_prob = dollarSpotProbability(avg_temp, avg_humidity)

        daily_weather = DailyWeatherData(
            date=converted_local_date,
            temp_max=max_temp,
            temp_min=min_temp,
            rain_sum=float(daily_rain_sum[i])
            if daily_rain_sum[i] is not None
            else None,
            sunshine_duration=float(daily_sunshine_duration[i])
            if daily_sunshine_duration[i] is not None
            else None,
            precip_prob_max=float(daily_precip_prob_max[i])
            if daily_precip_prob_max[i] is not None
            else None,
            uv_index_max=float(daily_uv_index_max[i])
            if daily_uv_index_max[i] is not None
            else None,
            et0_fao_evapotranspiration=float(daily_et0[i])
            if daily_et0[i] is not None
            else None,
            precipitation_sum=float(daily_precip_sum[i])
            if daily_precip_sum[i] is not None
            else None,
            precipitation_hours=float(daily_precip_hours[i])
            if daily_precip_hours[i] is not None
            else None,
            wind_direction_10m_dominant=float(daily_wind_speed_10m_max[i])
            if daily_wind_speed_10m_max[i] is not None
            else None,
            snowfall_sum=float(daily_snowfall_sum[i])
            if daily_snowfall_sum[i] is not None
            else None,
            cumulative_gdd=cumulative_gdd,
            gdd=daily_gdd,
            growth_potential=growth_potential,
            dollar_spot_probability=dollar_spot_prob,
        )
        session.add(daily_weather)
    session.commit()
    session.close()
    logger.info("Finished inserting daily weather records.")


def fetch_daily_forecast_weather(
    provider="openmeteo", lat=settings.DEFAULT_LATITUDE, lon=settings.DEFAULT_LONGITUDE
):
    session = SessionLocal()
    if provider.lower() == "openmeteo":
        weather_provider = OpenMeteoProvider()
        # Do not pass start_date/end_date so that the default 7-day forecast is returned.
        weather = weather_provider.get_daily_forecast_weather(
            lat=lat,
            lon=lon,
            timezone=settings.LOCAL_TIMEZONE,
            forecast_days=7,
        )
        if isinstance(weather, list):
            weather = weather[0]
    else:
        raise NotImplementedError("Only 'openmeteo' is supported")

    daily = weather.Daily()

    start_ts = daily.Time()  # Expected to be a single timestamp, e.g. 1742274000
    end_ts = daily.TimeEnd()  # Expected to be something like 1742878800
    interval = daily.Interval()  # Expected to be 86400

    daily_times = list(range(start_ts, end_ts, interval))
    logger.info(f"Calculated daily_times: {daily_times}")

    # Retrieve the daily variables from the forecast response.
    daily_temperature_2m_max = daily.Variables(0).ValuesAsNumpy()
    daily_temperature_2m_min = daily.Variables(1).ValuesAsNumpy()
    daily_rain_sum = daily.Variables(2).ValuesAsNumpy()
    daily_sunshine_duration = daily.Variables(3).ValuesAsNumpy()
    daily_precip_prob_max = daily.Variables(4).ValuesAsNumpy()
    daily_uv_index_max = daily.Variables(5).ValuesAsNumpy()
    daily_et0 = daily.Variables(6).ValuesAsNumpy()
    daily_precip_sum = daily.Variables(7).ValuesAsNumpy()
    daily_precip_hours = daily.Variables(8).ValuesAsNumpy()
    daily_wind_speed_10m_max = daily.Variables(9).ValuesAsNumpy()
    daily_snowfall_sum = daily.Variables(10).ValuesAsNumpy()

    # Process hourly humidity data for forecast
    hourly = weather.Hourly()

    # Fix for 'int' object is not iterable error
    hourly_start_ts = hourly.Time()  # Start timestamp
    hourly_end_ts = hourly.TimeEnd()  # End timestamp
    hourly_interval = hourly.Interval()  # Interval between timestamps

    # Create a list of timestamps using range
    hourly_times = list(range(hourly_start_ts, hourly_end_ts, hourly_interval))

    hourly_humidity = hourly.Variables(0).ValuesAsNumpy()

    # Group by day
    daily_humidity_avg = {}
    for i, ts in enumerate(hourly_times):
        if i < len(hourly_humidity) and hourly_humidity[i] is not None:
            utc_date = datetime.fromtimestamp(ts, tz=timezone.utc)
            date_key = utc_date.astimezone(ZoneInfo(settings.LOCAL_TIMEZONE)).date()

            if date_key not in daily_humidity_avg:
                daily_humidity_avg[date_key] = {"sum": 0, "count": 0}

            daily_humidity_avg[date_key]["sum"] += hourly_humidity[i]
            daily_humidity_avg[date_key]["count"] += 1

    # Calculate averages
    for date_key in daily_humidity_avg:
        if daily_humidity_avg[date_key]["count"] > 0:
            daily_humidity_avg[date_key] = (
                daily_humidity_avg[date_key]["sum"]
                / daily_humidity_avg[date_key]["count"]
            )
        else:
            daily_humidity_avg[date_key] = None

    # Loop through forecast days and calculate forecast values.
    for i, ts in enumerate(daily_times):
        # Convert timestamp as before
        utc_date = datetime.fromtimestamp(ts, tz=timezone.utc)
        converted_local_date = utc_date.astimezone(
            ZoneInfo(settings.LOCAL_TIMEZONE)
        ).date()

        max_temp = (
            float(daily_temperature_2m_max[i])
            if daily_temperature_2m_max[i] is not None
            else None
        )
        min_temp = (
            float(daily_temperature_2m_min[i])
            if daily_temperature_2m_min[i] is not None
            else None
        )

        forecast_gdd = None
        forecast_growth_potential = None
        if max_temp is not None and min_temp is not None:
            avg_temp = (max_temp + min_temp) / 2
            forecast_gdd = float(round(growingDegreeDays(avg_temp), 2))
            forecast_growth_potential = float(round(growthPotential(avg_temp), 2))

        avg_humidity = daily_humidity_avg.get(converted_local_date, None)

        dollar_spot_prob = None
        if max_temp is not None and min_temp is not None and avg_humidity is not None:
            avg_temp = (max_temp + min_temp) / 2
            dollar_spot_prob = dollarSpotProbability(avg_temp, avg_humidity)

        # Create an instance with new forecast data.
        forecast_instance = DailyForecastWeatherData(
            date=converted_local_date,
            temp_max=max_temp,
            temp_min=min_temp,
            rain_sum=float(daily_rain_sum[i])
            if daily_rain_sum[i] is not None
            else None,
            sunshine_duration=float(daily_sunshine_duration[i])
            if daily_sunshine_duration[i] is not None
            else None,
            precip_prob_max=float(daily_precip_prob_max[i])
            if daily_precip_prob_max[i] is not None
            else None,
            uv_index_max=float(daily_uv_index_max[i])
            if daily_uv_index_max[i] is not None
            else None,
            et0_fao_evapotranspiration=float(daily_et0[i])
            if daily_et0[i] is not None
            else None,
            precipitation_sum=float(daily_precip_sum[i])
            if daily_precip_sum[i] is not None
            else None,
            precipitation_hours=float(daily_precip_hours[i])
            if daily_precip_hours[i] is not None
            else None,
            wind_direction_10m_dominant=float(daily_wind_speed_10m_max[i])
            if daily_wind_speed_10m_max[i] is not None
            else None,
            snowfall_sum=float(daily_snowfall_sum[i])
            if daily_snowfall_sum[i] is not None
            else None,
            forecast_gdd=forecast_gdd,
            forecast_growth_potential=forecast_growth_potential,
            forecast_dollar_spot_probability=dollar_spot_prob,
        )

        # Use merge to upsert the record
        session.merge(forecast_instance)

    session.commit()
    session.close()
    logger.info("Finished inserting daily forecast weather records.")


def fetch_weather_data(start_date, end_date):
    for single_date in (
        start_date + timedelta(n) for n in range((end_date - start_date).days + 1)
    ):
        fetch_daily_weather(single_date, single_date)


def fetch_initial_data():
    logger.info("Fetching initial data")
    end_date = datetime.now(ZoneInfo(settings.LOCAL_TIMEZONE)) - timedelta(days=1)
    start_date = end_date - timedelta(days=30)
    logger.info(f"Fetching data from {start_date} to {end_date}")
    fetch_weather_data(start_date, end_date)
    logger.info("Initial data fetched")


def schedule_daily_fetch():
    logger.info("Scheduling daily fetch task")

    def daily_fetch_wrapper():
        logger.info("Executing daily fetch task")
        last_fetch_time = read_last_fetch_time()
        if last_fetch_time:
            start_date = last_fetch_time
        else:
            start_date = datetime.now(ZoneInfo(settings.LOCAL_TIMEZONE)) - timedelta(
                days=1
            )
        end_date = datetime.now(ZoneInfo(settings.LOCAL_TIMEZONE))
        fetch_daily_weather(start_date, end_date)
        fetch_daily_forecast_weather()
        write_last_fetch_time(end_date)

    scheduler.add_job(daily_fetch_wrapper, "cron", hour=1, minute=0)
    if not scheduler.running:
        scheduler.start()
        logger.info("Daily fetch scheduler started")

    logger.info("Daily fetch task scheduled")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    session = SessionLocal()
    if not session.query(DailyWeatherData).first():
        fetch_initial_data()
        write_last_fetch_time(
            datetime.now(ZoneInfo(settings.LOCAL_TIMEZONE)) - timedelta(days=1)
        )
    session.close()
    if not session.query(DailyForecastWeatherData).first():
        fetch_daily_forecast_weather()
    schedule_daily_fetch()


@app.get("/")
async def get_main():
    return "Hello, World!"


@app.post("/api/fetch-forecast")
async def manual_fetch_forecast():
    fetch_daily_forecast_weather()
    return {"message": "Forecast data fetched successfully"}


@app.get("/api/daily-forecast")
async def get_daily_forecast_data():
    session = SessionLocal()
    data = session.query(DailyForecastWeatherData).all()
    session.close()
    return data


@app.post("/api/reset-gdd")
async def reset_gdd():
    session = SessionLocal()
    # For simplicity, assume reset means that future cumulative calculations start at 0.
    # One approach: store a global reset in the database, or update a config file.
    # Here we'll update all records (or at least the latest one) to have cumulative_gdd = 0
    latest_record = (
        session.query(DailyWeatherData).order_by(DailyWeatherData.date.desc()).first()
    )
    if latest_record:
        latest_record.cumulative_gdd = 0.0
        session.commit()
    session.close()
    return {"message": "Cumulative GDD has been reset."}


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
