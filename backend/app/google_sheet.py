import json
import os
from pathlib import Path
from datetime import datetime

import gspread
import pandas as pd
from dotenv import load_dotenv
from google.oauth2.service_account import Credentials
from gspread.exceptions import SpreadsheetNotFound

from app.utils import logger

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

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
# Render (production): raw JSON content in GOOGLE_CREDENTIALS_JSON env var.
# Local dev: path to a JSON file via GOOGLE_CREDENTIALS_FILE in backend/.env.
CREDS_JSON = os.getenv("GOOGLE_CREDENTIALS_JSON", "").strip()
CREDS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "").strip()

if CREDS_JSON:
    creds_info = json.loads(CREDS_JSON)
    creds = Credentials.from_service_account_info(creds_info, scopes=scope)
elif CREDS_FILE:
    creds = Credentials.from_service_account_file(
        str((BASE_DIR / CREDS_FILE).resolve()), scopes=scope
    )
else:
    raise RuntimeError(
        "No Google credentials configured. Set GOOGLE_CREDENTIALS_JSON "
        "(raw service account JSON) or GOOGLE_CREDENTIALS_FILE (path to a "
        "local JSON file) in the environment."
    )

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


# def append_new_patients(clean_df):
#     master = read_master()

#     if master.empty:
#         master = pd.DataFrame(columns=MASTER_COLUMNS)

#     # Build unique keys for existing records
#     if not master.empty:
#         master["Unique Key"] = (
#             master["Patient First Name"].astype(str).str.strip().str.lower()
#             + "|"
#             + master["Patient Email"].astype(str).str.strip().str.lower()
#             + "|"
#             + master["Appointment Provider Name"].astype(str).str.strip().str.lower()
#             + "|"
#             + master["Appointment Date"].astype(str).str.strip()
#         )

#         existing_keys = set(master["Unique Key"])
#     else:
#         existing_keys = set()


#     today = datetime.today().strftime("%Y-%m-%d")

#     if "Appointment Date" not in clean_df.columns:
#         clean_df["Appointment Date"] = today

#     # Ensure expected columns exist
#     for col in MASTER_COLUMNS:
#         if col not in master.columns:
#             master[col] = ""

#     #existing_emails = set(master["Email"].astype(str).str.lower().values)
#     srn_series = pd.to_numeric(master["SRN"], errors="coerce")
#     next_srn = int(srn_series.max()) + 1 if srn_series.notna().any() else 1

#     new_rows = []

#     for _, row in clean_df.iterrows():

#         email = row.get("Patient E-mail") or row.get("Patient Email")

#         if not email:
#             continue

#         email = str(email).strip().lower()
#         provider = str(row.get("Appointment Provider Name", "")).strip()
#         if not provider:
#             provider = "NIH"

#         # if email and email not in existing_emails:
#         #     new_rows.append([
#         #         next_srn,
#         #         row.get("Patient First Name"),
#         #         email,
#         #         provider,
#         #         row.get("Appointment Date", today),
#         #     ])
#         #     next_srn += 1

#     if new_rows:
#         logger.info(f"Adding {len(new_rows)} new patients")

#         new_df = pd.DataFrame(new_rows, columns=MASTER_COLUMNS)
#         master = pd.concat([master, new_df], ignore_index=True)
#         master = master[MASTER_COLUMNS]
#         save_master(master)
#     else:
#         logger.info("No new patients found")

#     return master


def append_new_patients(clean_df):
    master = read_master()

    if master.empty:
        master = pd.DataFrame(columns=MASTER_COLUMNS)

    # Ensure all expected columns exist
    for col in MASTER_COLUMNS:
        if col not in master.columns:
            master[col] = ""

    # -----------------------------
    # Normalize Master Sheet
    # -----------------------------
    master["Name"] = master["Name"].astype(str).str.strip()
    master["Email"] = master["Email"].astype(str).str.strip().str.lower()
    master["Doc Name"] = master["Doc Name"].astype(str).str.strip()

    master["Date"] = (
        pd.to_datetime(master["Date"], errors="coerce")
        .dt.strftime("%Y-%m-%d")
        .fillna("")
    )

    # -----------------------------
    # Build Existing Keys
    # -----------------------------
    existing_keys = set()

    for _, row in master.iterrows():
        existing_keys.add((
            row["Name"].lower(),
            row["Email"],
            row["Doc Name"].lower(),
            row["Date"]
        ))

    # -----------------------------
    # Next SRN
    # -----------------------------
    srn = pd.to_numeric(master["SRN"], errors="coerce")

    if srn.notna().any():
        next_srn = int(srn.max()) + 1
    else:
        next_srn = 1

    # -----------------------------
    # Add New Patients
    # -----------------------------
    new_rows = []

    for _, row in clean_df.iterrows():

        patient_name = str(
            row.get("Patient First Name", "")
        ).strip()

        email = str(
            row.get("Patient E-mail")
            or row.get("Patient Email")
            or ""
        ).strip().lower()

        provider = str(
            row.get("Appointment Provider Name", "")
        ).strip()

        appointment_date = (
            pd.to_datetime(
                row.get("Appointment Date", ""),
                errors="coerce"
            )
            .strftime("%Y-%m-%d")
            if pd.notna(pd.to_datetime(row.get("Appointment Date", ""), errors="coerce"))
            else ""
        )

        if not patient_name or not email:
            continue

        unique_key = (
            patient_name.lower(),
            email,
            provider.lower(),
            appointment_date
        )

        # Skip duplicate
        if unique_key in existing_keys:
            logger.info(f"Duplicate skipped: {patient_name} | {email}")
            continue

        existing_keys.add(unique_key)

        new_rows.append([
            next_srn,
            patient_name,
            email,
            provider,
            appointment_date
        ])

        next_srn += 1

    # -----------------------------
    # Save
    # -----------------------------
    if new_rows:
        logger.info(f"Adding {len(new_rows)} new patients")

        new_df = pd.DataFrame(
            new_rows,
            columns=MASTER_COLUMNS
        )

        master = pd.concat(
            [master, new_df],
            ignore_index=True
        )

        master = master[MASTER_COLUMNS]

        save_master(master)

    else:
        logger.info("No new patients found")

    return master