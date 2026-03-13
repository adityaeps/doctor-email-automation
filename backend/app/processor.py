
import os
import re
import zipfile
from datetime import datetime
from pathlib import Path

import pandas as pd

from app.utils import (
    normalize_string,
    clean_email,
    safe_filename,
    logger
)

PROVIDER_COL = "Appointment Provider Name"
DEFAULT_PROVIDER = "NIH"
OUTPUT_SRN_COL = "SRN"
OUTPUT_NAME_COL = "Name"
OUTPUT_EMAIL_COL = "Email"
APPT_DATE_COL = "Appointment Date"


def _extract_appt_date_from_filename(path: str) -> str:
    """
    Extract appointment date from filename.
    Expected patterns like: "YYYY-MM-DD", "MM-DD-YYYY", "MM DD", "MM-DD",
    "MM_DD", "MMDD" in the stem.
    Falls back to today's date if not found.
    """
    stem = Path(path).stem
    # 1) YYYY-MM-DD / YYYY_MM_DD / YYYY MM DD / YYYYMMDD
    match = re.search(
        r"(20\d{2})[\s\-_]?(0?[1-9]|1[0-2])[\s\-_]?([0-2]?\d|3[01])",
        stem
    )
    if match:
        year = int(match.group(1))
        month = int(match.group(2))
        day = int(match.group(3))
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            return datetime.today().strftime("%Y-%m-%d")

    # 2) MM-DD-YYYY / MM_DD_YYYY / MM DD YYYY / MMDDYYYY
    match = re.search(
        r"(0?[1-9]|1[0-2])[\s\-_]?([0-2]?\d|3[01])[\s\-_]?(20\d{2})",
        stem
    )
    if match:
        month = int(match.group(1))
        day = int(match.group(2))
        year = int(match.group(3))
        try:
            return datetime(year, month, day).strftime("%Y-%m-%d")
        except ValueError:
            return datetime.today().strftime("%Y-%m-%d")

    # 3) MM DD / MM-DD / MM_DD / MMDD (use current year)
    match = re.search(r"(0?[1-9]|1[0-2])[\s\-_]?([0-2]?\d|3[01])", stem)
    if not match:
        return datetime.today().strftime("%Y-%m-%d")

    month = int(match.group(1))
    day = int(match.group(2))
    year = datetime.today().year
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return datetime.today().strftime("%Y-%m-%d")


def process_excel(input_excel: str, output_dir: str) -> str:
    try:
        logger.info(f"Started processing file: {input_excel}")
        # Extract filename stem to append to doctor filenames
        stem = Path(input_excel).stem
        stem_safe = safe_filename(stem)

        # -----------------------------
        # Load Excel
        # -----------------------------
        df = pd.read_excel(input_excel, skiprows=8)
        logger.info(f"Excel loaded successfully. Rows: {len(df)}")

        # -----------------------------
        # FIX: Normalize provider column
        # -----------------------------
        if PROVIDER_COL not in df.columns:
            logger.warning(
                f"{PROVIDER_COL} column missing. "
                f"Defaulting all rows to '{DEFAULT_PROVIDER}'."
            )
            df[PROVIDER_COL] = DEFAULT_PROVIDER
        else:
            df[PROVIDER_COL] = (
                df[PROVIDER_COL]
                .fillna(DEFAULT_PROVIDER)
                .replace("", DEFAULT_PROVIDER)
                .astype(str)
            )

        # -----------------------------
        # Select required columns
        # -----------------------------
        df = df[
            ["Patient First Name", "Patient E-mail", PROVIDER_COL]
        ].copy()

        # Remove invlaid rows before cleaning to avoid losing data due to cleaning issues
        df = df.iloc[0:-4]

        # -----------------------------
        # Drop invalid rows
        # (DO NOT drop on provider)
        # -----------------------------
        before = len(df)
        df = df.dropna(subset=["Patient E-mail"])
        after = len(df)

        logger.info(f"Dropped {before - after} invalid rows")

        # -----------------------------
        # Clean columns
        # -----------------------------
        df["Patient First Name"] = normalize_string(df["Patient First Name"])
        df["Patient E-mail"] = clean_email(df["Patient E-mail"])
        df[PROVIDER_COL] = normalize_string(df[PROVIDER_COL])

        # -----------------------------
        # Appointment date from filename
        # -----------------------------
        appt_date = _extract_appt_date_from_filename(input_excel)
        df[APPT_DATE_COL] = appt_date

        # -----------------------------
        # Output directories
        # -----------------------------
        doctors_dir = os.path.join(output_dir, "doctors")
        os.makedirs(doctors_dir, exist_ok=True)

        # -----------------------------
        # Create doctor-wise files
        # (group-by already dynamic & safe)
        # -----------------------------
        for doctor, group in df.groupby(PROVIDER_COL, dropna=False):
            filename = safe_filename(doctor)
            if stem_safe:
                path = os.path.join(doctors_dir, f"{filename}_{stem_safe}.csv")
            else:
                path = os.path.join(doctors_dir, f"{filename}.csv")

            group_out = group[
                ["Patient First Name", "Patient E-mail"]
            ].copy()
            group_out = group_out.rename(
                columns={
                    "Patient First Name": OUTPUT_NAME_COL,
                    "Patient E-mail": OUTPUT_EMAIL_COL,
                }
            )
            group_out.insert(0, OUTPUT_SRN_COL, range(1, len(group_out) + 1))
            group_out.to_csv(path, index=False)

            logger.info(
                f"Created file for doctor '{doctor}' with {len(group)} records"
            )

        # -----------------------------
        # Save combined file
        # -----------------------------
        combined_path = os.path.join(output_dir, "all_doctors.csv")
        combined_out = df[
            ["Patient First Name", "Patient E-mail"]
        ].copy()
        combined_out = combined_out.rename(
            columns={
                "Patient First Name": OUTPUT_NAME_COL,
                "Patient E-mail": OUTPUT_EMAIL_COL,
            }
        )
        combined_out.insert(0, OUTPUT_SRN_COL, range(1, len(combined_out) + 1))
        combined_out.to_csv(combined_path, index=False)
        logger.info("Created combined all_doctors.csv")

        # -----------------------------
        # Zip files
        # -----------------------------
        zip_path = os.path.join(output_dir, "doctor_files.zip")
        with zipfile.ZipFile(zip_path, "w") as zipf:
            zipf.write(combined_path, "all_doctors.csv")

            for file in os.listdir(doctors_dir):
                zipf.write(
                    os.path.join(doctors_dir, file),
                    f"doctors/{file}"
                )

        logger.info("ZIP file created successfully")
        logger.info("Processing completed successfully")

        return zip_path, df

    except Exception:
        logger.exception("❌ Error occurred while processing excel")
        raise



# import pandas as pd
# import os
# import zipfile
# import io

# from app.utils import (
#     normalize_string,
#     clean_email,
#     safe_filename,
#     logger
# )

# PROVIDER_COL = "Appointment Provider Name"
# DEFAULT_PROVIDER = "NIH"


# from pathlib import Path

# def process_excel(input_excel: str, output_dir: str) -> str:
#     try:
#         logger.info(f"Started processing file: {input_excel}")

#         # Extract uploaded file base name (without extension)
#         base_filename = Path(input_excel).stem   # <-- THIS is important

#         # -----------------------------
#         # Load Excel
#         # -----------------------------
#         df = pd.read_excel(input_excel, skiprows=8)
#         logger.info(f"Excel loaded successfully. Rows: {len(df)}")
#         logger.info(f"Columns detected: {list(df.columns)}")

#         # -----------------------------
#         # Provider column handling
#         # -----------------------------
#         if PROVIDER_COL not in df.columns:
#             logger.warning(
#                 f"{PROVIDER_COL} missing. Defaulting to '{DEFAULT_PROVIDER}'."
#             )
#             df[PROVIDER_COL] = DEFAULT_PROVIDER
#         else:
#             df[PROVIDER_COL] = (
#                 df[PROVIDER_COL]
#                 .fillna(DEFAULT_PROVIDER)
#                 .replace("", DEFAULT_PROVIDER)
#                 .astype(str)
#             )

#         # -----------------------------
#         # Required columns
#         # -----------------------------
#         df = df[
#             ["Patient First Name", "Patient E-mail", PROVIDER_COL]
#         ].copy()

#         df = df.dropna(subset=["Patient E-mail"])

#         df["Patient First Name"] = normalize_string(df["Patient First Name"])
#         df["Patient E-mail"] = clean_email(df["Patient E-mail"])
#         df[PROVIDER_COL] = normalize_string(df[PROVIDER_COL])

#         # -----------------------------
#         # Zip
#         # -----------------------------
#         zip_path = os.path.join(
#             output_dir,
#             f"{base_filename}_doctor_files.zip"
#         )

#         with zipfile.ZipFile(zip_path, "w") as zipf:
#             # Combined file (no disk write)
#             combined_name = f"{base_filename}_all_doctors.csv"
#             combined_buf = io.StringIO()
#             df.to_csv(combined_buf, index=False)
#             zipf.writestr(combined_name, combined_buf.getvalue())

#             # Doctor-wise files (no disk write)
#             for doctor, group in df.groupby(PROVIDER_COL):
#                 safe_doctor = safe_filename(doctor)
#                 filename = f"{base_filename}_{safe_doctor}.csv"

#                 group_out = group[
#                     ["Patient First Name", "Patient E-mail"]
#                 ].copy()
#                 group_out.insert(0, "Sr No.", range(1, len(group_out) + 1))

#                 buf = io.StringIO()
#                 group_out.to_csv(buf, index=False)
#                 zipf.writestr(f"doctors/{filename}", buf.getvalue())

#                 logger.info(
#                     f"Added to ZIP: {filename} with {len(group)} records"
#                 )

#         logger.info("ZIP file created successfully")

#         return zip_path

#     except Exception:
#         logger.exception("Error occurred while processing excel")
#         raise
