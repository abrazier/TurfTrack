import os


class Config:
    DEBUG = True
    DATABASE_URL = os.getenv(
        "DATABASE_URL", "postgresql://postgres:password@localhost:5432/weatherdb"
    )
