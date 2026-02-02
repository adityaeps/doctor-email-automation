import re
import logging
import pandas as pd
from datetime import datetime
import os


# ==================================================
# UTILITY FUNCTIONS
# ==================================================

def normalize_string(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip()


def clean_email(series: pd.Series) -> pd.Series:
    return series.astype("string").str.strip().str.lower()


def safe_filename(name: str) -> str:
    return re.sub(r"[^\w\s-]", "", name).replace(" ", "_")
