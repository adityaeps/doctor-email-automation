
import pandas as pd
import os
import zipfile
from pathlib import Path

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

        return zip_path

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
