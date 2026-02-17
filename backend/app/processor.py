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




import pandas as pd
import os
import zipfile
import io
from pathlib import Path

from app.utils import (
    normalize_string,
    clean_email,
    safe_filename,
    logger
)

PROVIDER_COL = "Appointment Provider Name"
DEFAULT_PROVIDER = "NIH"


def process_excel(input_excel: str, output_dir: str) -> str:
    try:
        logger.info(f"Started processing file: {input_excel}")

        # Extract uploaded file base name (without extension)
        base_filename = Path(input_excel).stem

        # -----------------------------
        # Load Excel
        # -----------------------------
        df = pd.read_excel(input_excel, skiprows=8)
        logger.info(f"Excel loaded successfully. Rows: {len(df)}")
        logger.info(f"Columns detected: {list(df.columns)}")

        # Normalize column names to avoid hidden whitespace issues
        df.columns = df.columns.astype("string").str.strip()

        # -----------------------------
        # Provider column handling
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
                .astype("string")
                .str.strip()
                .fillna(DEFAULT_PROVIDER)
                .replace("", DEFAULT_PROVIDER)
            )

        # -----------------------------
        # Select required columns
        # -----------------------------
        df = df[
            ["Patient First Name", "Patient E-mail", PROVIDER_COL]
        ].copy()

        # Drop rows missing name/email
        df = df.dropna(subset=["Patient E-mail", "Patient First Name"])

        # Clean columns
        df["Patient First Name"] = normalize_string(df["Patient First Name"])
        df["Patient E-mail"] = clean_email(df["Patient E-mail"])
        df[PROVIDER_COL] = normalize_string(df[PROVIDER_COL])

        # Keep only rows with non-empty first name and email after trimming
        before = len(df)
        df = df[
            (df["Patient First Name"] != "") &
            (df["Patient E-mail"] != "")
        ]
        dropped_blank = before - len(df)
        if dropped_blank:
            logger.info(
                f"Dropped {dropped_blank} rows with blank name/email"
            )

        # Drop invalid emails (e.g., time-like values such as 16:00:09)
        before = len(df)
        email_pattern = r"^[^@\\s]+@[^@\\s]+\\.[^@\\s]+$"
        df = df[df["Patient E-mail"].str.contains(email_pattern, na=False)]
        dropped_email = before - len(df)
        if dropped_email:
            logger.info(f"Dropped {dropped_email} invalid email rows")

        # -----------------------------
        # Zip (write files directly, no disk CSVs)
        # -----------------------------
        zip_path = os.path.join(
            output_dir,
            f"{base_filename}_doctor_files.zip"
        )

        with zipfile.ZipFile(zip_path, "w") as zipf:
            # Combined file
            combined_name = f"{base_filename}_all_doctors.csv"
            combined_buf = io.StringIO()
            df.to_csv(combined_buf, index=False)
            zipf.writestr(combined_name, combined_buf.getvalue())

            # Doctor-wise files
            for doctor, group in df.groupby(PROVIDER_COL):
                safe_doctor = safe_filename(doctor)
                filename = f"{base_filename}_{safe_doctor}.csv"

                group_out = group[
                    ["Patient First Name", "Patient E-mail"]
                ].copy()
                group_out.insert(0, "Sr No.", range(1, len(group_out) + 1))

                buf = io.StringIO()
                group_out.to_csv(buf, index=False)
                zipf.writestr(f"doctors/{filename}", buf.getvalue())

                logger.info(
                    f"Added to ZIP: {filename} with {len(group)} records"
                )

        logger.info("ZIP file created successfully")
        logger.info("Processing completed successfully")

        return zip_path

    except Exception:
        logger.exception("❌ Error occurred while processing excel")
        raise
