from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from src.config import Config
from src.services.weather import OpenWeatherMapProvider

app = FastAPI(debug=Config.DEBUG)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Existing endpoints
@app.get("/")
async def get_main():
    return "Hello, World!"


@app.get("/api/gdd")
async def get_gdd():
    return {"gdd": 0}


@app.post("/api/fertilizer")
async def add_fertilizer_log(log: dict):
    return {"message": "Fertilizer log added", "data": log}


@app.get("/api/weather")
async def get_weather():
    try:
        provider = OpenWeatherMapProvider()
        return provider.get_weather()  # Returns Chicago's weather by default
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
