import re
import math
import pandas as pd


def normalize_ticker(ticker):
    """
    Standardize ticker symbol strings.
    Removes trailing/leading whitespace and formats correctly.
    """
    if pd.isna(ticker) or not isinstance(ticker, str):
        return None
    return ticker.strip().upper()


def normalize_year(year_val):
    """
    Normalizes year entries to a standard 4-digit integer year.
    Supports formats:
      - 'Dec 2012' -> 2012
      - 'Mar-13' -> 2013
      - 'Mar 2023 15' -> 2023
      - 'Mar 2016 9m' -> 2016
      - 2024 -> 2024
      - '2024' -> 2024
      - 'TTM' -> None (ignored/filtered)
    """
    if pd.isna(year_val):
        return None

    # Handle pure numeric type
    if isinstance(year_val, (int, float)):
        if math.isnan(year_val):
            return None
        return int(year_val)

    val_str = str(year_val).strip()

    if val_str.upper() == "TTM":
        return None

    # Match any 4-digit number (e.g. 2012, 2023)
    match_4digit = re.search(r"\b(20\d{2}|19\d{2})\b", val_str)
    if match_4digit:
        return int(match_4digit.group(1))

    # Match 2-digit abbreviation formats (e.g. Mar-13, Mar-14)
    match_2digit = re.search(
        r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[-/\s](\d{2})\b",
        val_str,
        re.IGNORECASE,
    )
    if match_2digit:
        yr_short = int(match_2digit.group(1))
        # standard epoch assumptions for Cohort 2025/2026 data
        return 2000 + yr_short if yr_short < 50 else 1900 + yr_short

    # Direct parse check if it's purely digits
    if val_str.isdigit():
        return int(val_str)

    return None
