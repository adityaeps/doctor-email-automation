# backend/app/campaign/constants.py

DAILY_LIMIT = 300

STATUS_PENDING = "PENDING"
STATUS_SENT = "SENT"
STATUS_FOLLOWUP7 = "FOLLOWUP7"
STATUS_FOLLOWUP14 = "FOLLOWUP14"
STATUS_COMPLETED = "COMPLETED"

FOLLOWUP_1_DAYS = 3
FOLLOWUP_2_DAYS = 7

COL_EMAIL = "Patient Email"
COL_NAME = "Patient First Name"
COL_DOCTOR = "Appointment Provider Name"
COL_FIRST_SEEN = "First Seen Date"
COL_STATUS = "Status"
COL_LAST_EMAIL = "Last Email Date"
COL_FOLLOWUP_COUNT = "Followup Count"
COL_EMAIL_COUNT = "Followup Count"


MASTER_PATH = "backend/data/master/master_patients.csv"
NO_REVIEW_PATH = "backend/data/no_review/latest_no_review.csv"

MASTER_COLUMNS = [
    COL_EMAIL,
    COL_NAME,
    COL_DOCTOR,
    COL_FIRST_SEEN,
    COL_STATUS,
    COL_LAST_EMAIL,
    COL_FOLLOWUP_COUNT,
]
