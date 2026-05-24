from sqlalchemy import create_engine
import pandas as pd
import logging
import os

logger = logging.getLogger(__name__)

def get_db_engine():
    
    user = os.getenv("DB_USER")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT")
    name = os.getenv("DB_NAME")

    connection_string = f"postgresql://{user}@{host}:{port}/{name}"
    return create_engine(connection_string)

def test_connection():
    try:
        engine = get_db_engine()
        with engine.connect() as connection:
            logger.info("[SUCCESS] Successfully connected to PostgreSQL!")
    except Exception as e:
        logger.warning(f"[FAILED] Could not connect to database: {e}")

if __name__ == "__main__":
    test_connection()