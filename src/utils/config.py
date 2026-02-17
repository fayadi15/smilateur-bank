import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_USER = os.getenv("DB_USER", "postgres")
    DB_PASS = os.getenv("DB_PASS", "password")
    DB_NAME = os.getenv("DB_NAME", "scoring_db")
    DB_PORT = os.getenv("DB_PORT", "5432")

    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
