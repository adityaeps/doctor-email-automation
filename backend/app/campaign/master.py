import pandas as pd
from datetime import datetime
from app.campaign.constants import *
from app.campaign.sheets import read_master_from_sheet, save_master_for_sheet
from app.logger import logger


def load_master() -> pd.DataFrame:
    """
    Always read latest master from Google Sheet
    """
    logger.info("Reading master from Google Sheet")
    df = read_master_from_sheet()

    if df.empty:
        logger.warning("Master sheet empty. Initializing columns.")
        df = pd.DataFrame(columns=MASTER_COLUMNS)

    return df


def save_master(df: pd.DataFrame):
    """
    Always save master back to Google Sheet
    """
    save_master_for_sheet(df)
    logger.info("Master saved to Google Sheet")


def append_new_patients(clean_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add new patients to master from daily excel
    """
    master = load_master()

    today = datetime.today().strftime("%Y-%m-%d")

    new_rows = []

    for _, row in clean_df.iterrows():
        email = row["Patient Email"]

        if email not in master[COL_EMAIL].values:
            new_rows.append([
                email,
                row["Patient First Name"],
                row["Appointment Provider Name"],
                today,
                STATUS_PENDING,
                "",
                0,
            ])

    if new_rows:
        logger.info(f"Adding {len(new_rows)} new patients to master")

        new_df = pd.DataFrame(new_rows, columns=MASTER_COLUMNS)
        master = pd.concat([master, new_df], ignore_index=True)

        save_master(master)

    else:
        logger.info("No new patients to add")

    return master
