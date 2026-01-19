import re
import logging
import pandas as pd
from datetime import datetime
import os


# ---------------- LOGGER SETUP ----------------

LOG_DIR = "backend/logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR,
    f"app_{datetime.now().strftime('%Y_%m_%d')}.log"
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)


# ---------------- UTILITY FUNCTIONS ----------------

def normalize_string(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def clean_email(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def safe_filename(name: str) -> str:
    return re.sub(r"[^\w\s-]", "", name).replace(" ", "_")
