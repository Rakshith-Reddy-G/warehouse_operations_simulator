# Configuration file for Warehouse Operations Simulator
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environmental variables from .env file
load_dotenv()

# Base paths
BASE_DIR = Path(__file__).resolve().parent
EXPORT_DIR = BASE_DIR / "sample_data"
EXPORT_DIR.mkdir(parents=True, exist_ok=True)

# Database Configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", 3306))
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "password")
DB_NAME = os.getenv("DB_NAME", "warehouse_db")

# Simulation Parameters
SIMULATION_SPEED_SECONDS = float(os.getenv("SIMULATION_SPEED_SECONDS", 1.0))
LOW_STOCK_THRESHOLD = int(os.getenv("LOW_STOCK_THRESHOLD", 15))
QA_FAIL_PROBABILITY = float(os.getenv("QA_FAIL_PROBABILITY", 0.05)) # 5% QA failure rate
RETURN_PROBABILITY = float(os.getenv("RETURN_PROBABILITY", 0.10)) # 10% returns

# Logging Config
LOG_FILE = BASE_DIR / "warehouse_simulator.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s"
