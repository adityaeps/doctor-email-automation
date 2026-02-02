import pandas as pd
from datetime import datetime
from app.campaign.constants import *
from app.campaign.master import load_master, save_master
from app.logger import logger


def process_no_review_file(path: str):
    try:
        logger.info("Processing no-review file with Post Date logic")

        df = pd.read_csv(path)

        # Get Post Date from CSV
        post_date_str = df["Post Date"].iloc[0]
        post_date = datetime.strptime(post_date_str, "%Y-%m-%d")

        no_review_emails = set(
            df["Email"].astype(str).str.lower().str.strip()
        )

        master = load_master()
        today = datetime.today()

        for i, row in master.iterrows():

            # 🔴 Stop forever after 14-day followup
            if row[COL_STATUS] == STATUS_FOLLOWUP14 and row[COL_EMAIL_COUNT] >= 3:
                continue

            last_email_str = row[COL_LAST_EMAIL]
            if not last_email_str:
                continue

            last_email_date = datetime.strptime(last_email_str, "%Y-%m-%d")

            # 🔴 Only evaluate those who were part of that campaign batch
            if last_email_date > post_date:
                continue

            email = row[COL_EMAIL]
            status = row[COL_STATUS]
            days_passed = (today - last_email_date).days

            if email not in no_review_emails:
                master.at[i, COL_STATUS] = STATUS_COMPLETED

            elif status == STATUS_SENT and days_passed >= FOLLOWUP_1_DAYS:
                master.at[i, COL_STATUS] = STATUS_FOLLOWUP7

            elif status == STATUS_FOLLOWUP7 and days_passed >= FOLLOWUP_2_DAYS:
                master.at[i, COL_STATUS] = STATUS_FOLLOWUP14

        save_master(master)
        logger.info("Follow-up processing completed correctly")

    except Exception:
        logger.exception("Error processing no-review file")
