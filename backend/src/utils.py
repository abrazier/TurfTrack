import os
from datetime import datetime

LAST_FETCH_FILE = "last_fetch_time.txt"


def read_last_fetch_time():
    if os.path.exists(LAST_FETCH_FILE):
        with open(LAST_FETCH_FILE, "r") as file:
            return datetime.fromisoformat(file.read().strip())
    return None


def write_last_fetch_time(fetch_time):
    with open(LAST_FETCH_FILE, "w") as file:
        file.write(fetch_time.isoformat())
