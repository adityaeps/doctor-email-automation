import pandas as pd

from app.logger import logger
from app.utils import normalize_string, clean_email  # ✅ MISSING IMPORT


PROVIDER_COL = "Appointment Provider Name"
DEFAULT_PROVIDER = "NIH"


def process_excel(input_excel: str) -> pd.DataFrame:
    """
    Phase 1:
    Read Excel → Clean → Return clean dataframe
    """

    try:
        logger.info(f"Started processing file: {input_excel}")

        # -----------------------------
        # Load Excel
        # -----------------------------
        df = pd.read_excel(input_excel, skiprows=8)
        logger.info(f"Excel loaded successfully. Rows: {len(df)}")

        # -----------------------------
        # Normalize provider column
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
        # Drop invalid rows (email only)
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

        # Standardize column name for campaign engine
        df = df.rename(columns={"Patient E-mail": "Patient Email"})

        logger.info("Excel cleaned successfully. Returning dataframe.")
 
        return df

    except Exception:
        logger.exception("❌ Error occurred while processing excel")
        raise
