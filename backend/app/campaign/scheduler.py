import pandas as pd
from datetime import datetime
from app.campaign.constants import *
from app.logger import logger


def build_today_list(master: pd.DataFrame) -> pd.DataFrame:
    logger.info("Building today's 300 email list")

    # 🔴 Remove patients who completed 14-day cycle
    master = master[
        ~(
            (master[COL_STATUS] == STATUS_FOLLOWUP14) &
            (master[COL_EMAIL_COUNT] >= 3)
        )
    ]

    # Priority order
    pending = master[master[COL_STATUS] == STATUS_PENDING]
    f7 = master[master[COL_STATUS] == STATUS_FOLLOWUP7]
    f14 = master[master[COL_STATUS] == STATUS_FOLLOWUP14]

    # Oldest first
    pending = pending.sort_values(COL_FIRST_SEEN)
    f7 = f7.sort_values(COL_LAST_EMAIL)
    f14 = f14.sort_values(COL_LAST_EMAIL)

    today_list = pd.concat([pending, f7, f14]).head(300)

    logger.info(f"Today's list created with {len(today_list)} patients")

    today = datetime.today().strftime("%Y-%m-%d")

    # Update status for selected
    for i in today_list.index:
        status = master.at[i, COL_STATUS]

        if status == STATUS_PENDING:
            master.at[i, COL_STATUS] = STATUS_SENT
        elif status == STATUS_FOLLOWUP7:
            master.at[i, COL_STATUS] = STATUS_FOLLOWUP14

        master.at[i, COL_LAST_EMAIL] = today
        master.at[i, COL_EMAIL_COUNT] += 1

    return today_list, master
