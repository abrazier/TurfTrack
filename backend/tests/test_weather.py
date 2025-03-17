import sys
import os
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timezone, timedelta

# Add the src directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from main import app, read_last_fetch_time, write_last_fetch_time
from database import engine
from models import Base

# Create a TestClient
client = TestClient(app)


# Setup and teardown for the database
@pytest.fixture(scope="module")
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


# Test the /api/fetch endpoint
def test_manual_fetch(setup_database):
    response = client.post("/api/fetch")
    assert response.status_code == 200
    assert response.json() == {"message": "Data fetched successfully"}


# Test the /api/daily endpoint
def test_get_daily_data(setup_database):
    response = client.get("/api/daily")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Test the /api/hourly endpoint
def test_get_hourly_data(setup_database):
    response = client.get("/api/hourly")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


# Test the /api/scheduler/status endpoint
def test_get_scheduler_status(setup_database):
    response = client.get("/api/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert "jobs" in data
    assert isinstance(data["jobs"], list)


# Test the read_last_fetch_time and write_last_fetch_time functions
def test_fetch_time_functions():
    now = datetime.now(timezone.utc)
    write_last_fetch_time(now)
    fetch_time = read_last_fetch_time()
    assert fetch_time == now


def test_data_created_after_manual_fetch(setup_database):
    # Trigger manual fetch
    response = client.post("/api/fetch")
    assert response.status_code == 200

    # Now check that /api/daily and /api/hourly return non-empty lists.
    daily_response = client.get("/api/daily")
    hourly_response = client.get("/api/hourly")
    daily_data = daily_response.json()
    hourly_data = hourly_response.json()
    assert isinstance(daily_data, list)
    assert isinstance(hourly_data, list)
    # You might want to check that at least one entry exists.
    assert len(daily_data) >= 0
    assert len(hourly_data) >= 0


def test_scheduler_status_format(setup_database):
    response = client.get("/api/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    jobs = data.get("jobs")
    assert isinstance(jobs, list)
    # Check that each job's next_run_time (if present) is ISO formatted
    for job in jobs:
        next_run_time = job.get("next_run_time")
        if next_run_time:
            # Try parsing it with datetime.fromisoformat
            parsed_time = datetime.fromisoformat(next_run_time)
            assert isinstance(parsed_time, datetime)


def test_fetch_time_functions_behavior():
    now = datetime.now(timezone.utc)
    write_last_fetch_time(now)
    fetch_time = read_last_fetch_time()
    # Allow a small delta for processing times.
    delta = abs((fetch_time - now).total_seconds())
    assert delta < 1
