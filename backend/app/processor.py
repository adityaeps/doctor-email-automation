import pandas as pd
import os
import zipfile

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
            path = os.path.join(doctors_dir, f"{filename}.csv")

            group_out = group[
                ["Patient First Name", "Patient E-mail"]
            ].copy()
            group_out.insert(0, "Sr No.", range(1, len(group_out) + 1))
            group_out.to_csv(path, index=False)

            logger.info(
                f"Created file for doctor '{doctor}' with {len(group)} records"
            )

        # -----------------------------
        # Save combined file
        # -----------------------------
        combined_path = os.path.join(output_dir, "all_doctors.csv")
        df.to_csv(combined_path, index=False)
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
