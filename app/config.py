import os
from dotenv import load_dotenv

load_dotenv()

# Get the base directory of the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# --- Database Configuration ---
# Use an environment variable for the database URL for production deployments with a sensible default for local development.
DATABASE_URL = os.getenv("DATABASE_URL",
                         "postgresql://digiflow_user:Password2005@localhost/digiflow_db")

# --- Scheduler Configuration ---
DEFAULT_SOLVER_TIMEOUT_SECONDS = 120.0
BASE_SOLVER_TIMEOUT = 30.0
TIMEOUT_PER_TASK = 0.5

# --- Mock Data Paths (for seeding/testing) ---
MOCK_DATA_PATH = os.path.join(BASE_DIR, 'mock_data')

MACHINE_CSV = os.path.join(MOCK_DATA_PATH, 'machine_catalog_mock_data.csv')
PROCESS_STEP_CSV = os.path.join(MOCK_DATA_PATH, 'process_route_mock_data.csv')
PRODUCTION_ORDER_CSV = os.path.join(MOCK_DATA_PATH, 'production_job_schedule_mock_data.csv')
DOWNTIME_EVENT_CSV = os.path.join(MOCK_DATA_PATH, 'downtime_events_mock_data.csv')

# --- Other Potential configs ---
# API_PREFIX = "/api/v1"
# DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"
# LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
