import logging
import os
from datetime import datetime

LOG_DIR = "backend/logs"
os.makedirs(LOG_DIR, exist_ok=True)

LOG_FILE = os.path.join(
    LOG_DIR,
    f"app_{datetime.now().strftime('%Y_%m_%d')}.log"
)

# 🔥 Clear any existing logging config completely
for handler in logging.root.handlers[:]:
    logging.root.removeHandler(handler)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)
logger.info("Fresh logger initialized")
