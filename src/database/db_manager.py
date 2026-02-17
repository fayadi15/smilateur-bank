import psycopg2
import json
from psycopg2.extras import Json
from ..utils.config import Config
from ..utils.logger import setup_logger

logger = setup_logger(__name__)

class DatabaseManager:
    def __init__(self):
        self.conn = None
        self.connect()

    def connect(self):
        try:
            self.conn = psycopg2.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASS,
                dbname=Config.DB_NAME,
                port=Config.DB_PORT
            )
            # Enable autocommit for simplicity in this script, or manage transactions explicitly
            self.conn.autocommit = True
            logger.info("Connected to Database")
        except Exception as e:
            logger.error(f"Error connecting to database: {e}")
            raise

    def init_db(self):
        """Creates the necessary tables if they don't exist."""
        create_table_query = """
        CREATE TABLE IF NOT EXISTS scoring_logs (
            id SERIAL PRIMARY KEY,
            profile_data JSONB,
            bank_name VARCHAR(50),
            result_status VARCHAR(20),
            monthly_payment DECIMAL(10, 2),
            interest_rate DECIMAL(5, 2),
            scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(create_table_query)
                logger.info("Table 'scoring_logs' checked/created.")
        except Exception as e:
            logger.error(f"Error initializing DB: {e}")

    def insert_result(self, profile_data: dict, bank_name: str, result_status: str, 
                      monthly_payment: float = None, interest_rate: float = None):
        """Inserts a scraping result into the database."""
        insert_query = """
        INSERT INTO scoring_logs (profile_data, bank_name, result_status, monthly_payment, interest_rate)
        VALUES (%s, %s, %s, %s, %s);
        """
        try:
            with self.conn.cursor() as cur:
                cur.execute(insert_query, (
                    Json(profile_data),
                    bank_name,
                    result_status,
                    monthly_payment,
                    interest_rate
                ))
            logger.debug(f"Result saved for profile {profile_data.get('id', 'unknown')}")
        except Exception as e:
            logger.error(f"Error inserting result: {e}")

    def clear_logs(self):
        """Deletes all records from scoring_logs table."""
        try:
            with self.conn.cursor() as cur:
                cur.execute("TRUNCATE TABLE scoring_logs;")
                logger.info("Table 'scoring_logs' truncated (cleared).")
        except Exception as e:
            logger.error(f"Error clearing logs: {e}")

    def close(self):
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed.")
