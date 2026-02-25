import os
from pathlib import Path
from datetime import datetime

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound

from app.utils import logger

BASE_DIR = Path(__file__).resolve().parent.parent

SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "").strip()
DEFAULT_SHEET_URL = (
    "https://docs.google.com/spreadsheets/d/"
    "1b2WYf4KdGqF8XEcpYWuIrJSqA7jPE3_WPk4dLbpQ--A/edit"
)
DEFAULT_SHEET_NAME = "Master"

SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "").strip()
SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "").strip() or DEFAULT_SHEET_URL
_sheet_name = os.getenv("GOOGLE_SHEET_NAME", "").strip()
SHEET_NAME = _sheet_name or DEFAULT_SHEET_NAME

MASTER_COLUMNS = [
    "Patient Email",
    "Patient First Name",
    "Appointment Provider Name",
    "First Seen Date",
    "Status",
    "Last Email Date",
    "Followup Count"
]

# Google Auth
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "old_credentials.json").strip()
CREDS_PATH = (BASE_DIR / CREDS_FILE).resolve()

creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=scope)

client = gspread.authorize(creds)


def _get_sheet():
    try:
        return client.open_by_key(
            "1b2WYf4KdGqF8XEcpYWuIrJSqA7jPE3_WPk4dLbpQ--A"
        ).worksheet(SHEET_NAME)
    except SpreadsheetNotFound as exc:
        raise ValueError(
            f"Sheet not found or not shared with {creds.service_account_email}"
        ) from exc


def read_master():
    logger.info("Reading master sheet")
    sheet = _get_sheet()
    data = sheet.get_all_records()
    return pd.DataFrame(data)


def save_master(df):
    logger.info("Saving master sheet")
    sheet = _get_sheet()
    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())


def append_new_patients(clean_df):
    master = read_master()

    if master.empty:
        master = pd.DataFrame(columns=MASTER_COLUMNS)

    today = datetime.today().strftime("%Y-%m-%d")

    new_rows = []

    for _, row in clean_df.iterrows():
        email = row["Patient E-mail"]

        if email not in master["Patient Email"].values:
            new_rows.append([
                email,
                row["Patient First Name"],
                row["Appointment Provider Name"],
                today,
                "Pending",
                "",
                0
            ])

    if new_rows:
        logger.info(f"Adding {len(new_rows)} new patients")

        new_df = pd.DataFrame(new_rows, columns=MASTER_COLUMNS)
        master = pd.concat([master, new_df], ignore_index=True)
        save_master(master)
    else:
        logger.info("No new patients found")

    return master
