import os
from pathlib import Path
from datetime import datetime

import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound

from app.utils import logger

BASE_DIR = Path(__file__).resolve().parent.parent

# Default Google Sheet configuration
DEFAULT_SHEET_URL = "https://docs.google.com/spreadsheets/d/1Tol4Ybh3SOjMeOSM0VMev86ebiKZuYoHR7TQz1q5cDA/edit?gid=2106247609#gid=2106247609"
DEFAULT_SHEET_NAME = "Master"

# Environment overrides (optional)
SHEET_URL = os.getenv("GOOGLE_SHEET_URL", "").strip() or DEFAULT_SHEET_URL
_sheet_name = os.getenv("GOOGLE_SHEET_NAME", "").strip()
SHEET_NAME = _sheet_name or DEFAULT_SHEET_NAME

MASTER_COLUMNS = [
    "SRN",
    "Name",
    "Email",
    "Doc Name",
    "Date",
]

# Google API scope
scope = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive"
]

# Credentials
CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "old_credentials.json").strip()
CREDS_PATH = (BASE_DIR / CREDS_FILE).resolve()

creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=scope)
client = gspread.authorize(creds)


def _extract_sheet_id():
    """Extract sheet ID from the Google Sheet URL"""
    return SHEET_URL.split("/d/")[1].split("/")[0]


def _get_sheet():
    try:
        sheet_id = _extract_sheet_id()
        return client.open_by_key(sheet_id).worksheet(SHEET_NAME)
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

    if df.empty:
        sheet.clear()
        return

    sheet.clear()
    sheet.update([df.columns.values.tolist()] + df.values.tolist())


def append_new_patients(clean_df):
    master = read_master()

    if master.empty:
        master = pd.DataFrame(columns=MASTER_COLUMNS)

    today = datetime.today().strftime("%Y-%m-%d")

    if "Appointment Date" not in clean_df.columns:
        clean_df["Appointment Date"] = today

    # Ensure expected columns exist
    for col in MASTER_COLUMNS:
        if col not in master.columns:
            master[col] = ""

    existing_emails = set(master["Email"].astype(str).str.lower().values)
    srn_series = pd.to_numeric(master["SRN"], errors="coerce")
    next_srn = int(srn_series.max()) + 1 if srn_series.notna().any() else 1

    new_rows = []

    for _, row in clean_df.iterrows():

        email = row.get("Patient E-mail") or row.get("Patient Email")

        if not email:
            continue

        email = str(email).strip().lower()
        provider = str(row.get("Appointment Provider Name", "")).strip()
        if not provider:
            provider = "NIH"

        if email and email not in existing_emails:
            new_rows.append([
                next_srn,
                row.get("Patient First Name"),
                email,
                provider,
                row.get("Appointment Date", today),
            ])
            next_srn += 1

    if new_rows:
        logger.info(f"Adding {len(new_rows)} new patients")

        new_df = pd.DataFrame(new_rows, columns=MASTER_COLUMNS)
        master = pd.concat([master, new_df], ignore_index=True)
        master = master[MASTER_COLUMNS]
        save_master(master)
    else:
        logger.info("No new patients found")

    return master
