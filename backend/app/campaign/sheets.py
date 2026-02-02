import gspread # type: ignore
import pandas as pd
from pathlib import Path
from google.oauth2.service_account import Credentials # type: ignore
from app.logger import logger

SHEET_URL = "https://docs.google.com/spreadsheets/d/1b2WYf4KdGqF8XEcpYWuIrJSqA7jPE3_WPk4dLbpQ--A/edit?gid=0#gid=0"
SHEET_NAME = "Master"

scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Absolute path to backend/
BASE_DIR = Path(__file__).resolve().parents[2]

CREDENTIALS_PATH = BASE_DIR / "credentials.json"

logger.info(f"Using credentials at: {CREDENTIALS_PATH}")

creds = Credentials.from_service_account_file(
    CREDENTIALS_PATH,
    scopes=scope
)

client = gspread.authorize(creds)



def read_master_from_sheet() -> pd.DataFrame:
    logger.info("Reading master from Google Sheet via API")
    sheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)
    data = sheet.get_all_records()
    return pd.DataFrame(data)


def save_master_for_sheet(df: pd.DataFrame):
    logger.info("Writing master back to Google Sheet via API")

    sheet = client.open_by_url(SHEET_URL).worksheet(SHEET_NAME)

    # CRITICAL FIX — remove pandas NA/NaN
    clean_df = df.fillna("").astype(str)

    sheet.clear()
    sheet.update(
        [clean_df.columns.values.tolist()] + clean_df.values.tolist()
    )

