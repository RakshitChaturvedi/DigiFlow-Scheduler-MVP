import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))

from backend.app.database import create_tables
from backend.app.config import DATABASE_URL
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

if __name__ == "__main__":
    logging.info(f"Attempting to set up database at: {DATABASE_URL}")
    try:
        create_tables()
        logging.info("Database schema created successfully.")
    except Exception as e:
        logging.error(f"Error creating database tables: {e}", exc_info=True)