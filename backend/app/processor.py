import pandas as pd
import os
import zipfile

from app.utils import (
    normalize_string,
    clean_email,
    safe_filename,
    logger
)


def process_excel(input_excel: str, output_dir: str) -> str:
    try:
        logger.info(f"Started processing file: {input_excel}")

        # Load Excel
        df = pd.read_excel(input_excel, skiprows=8)
        logger.info(f"Excel loaded successfully. Rows: {len(df)}")

        # Select required columns
        df = df[
            ["Patient First Name", "Patient E-mail", "Appointment Provider Name"]
        ].copy()

        # Drop invalid rows
        before = len(df)
        df = df.dropna(subset=["Patient E-mail", "Appointment Provider Name"])
        after = len(df)

        logger.info(f"Dropped {before - after} invalid rows")

        # Clean columns
        df["Patient First Name"] = normalize_string(df["Patient First Name"])
        df["Patient E-mail"] = clean_email(df["Patient E-mail"])
        df["Appointment Provider Name"] = normalize_string(
            df["Appointment Provider Name"]
        )

        # Ensure required columns exist
        required_columns = ["Patient First Name", "Patient E-mail", "Appointment Provider Name"]
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            raise KeyError(f"Missing required columns: {missing_columns}")

        doctors_dir = os.path.join(output_dir, "doctors")
        os.makedirs(doctors_dir, exist_ok=True)

        # Create doctor-wise files
        for doctor, group in df.groupby("Appointment Provider Name"):
            filename = safe_filename(doctor)
            path = os.path.join(doctors_dir, f"{filename}.csv")

            group[
                ["Patient First Name", "Patient E-mail"]
            ].to_csv(path, index=False)

            logger.info(
                f"Created file for doctor '{doctor}' with {len(group)} records"
            )

        # Save combined file
        combined_path = os.path.join(output_dir, "all_doctors.csv")
        df.to_csv(combined_path, index=False)
        logger.info("Created combined all_doctors.csv")

        # Zip files
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

    except Exception as e:
        logger.exception("❌ Error occurred while processing excel")
        raise e
