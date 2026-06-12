import re
from pathlib import Path

# Quick lookup to translate English short months to zero-padded numeric strings
_MONTH_TO_NUM = {
    "Jan": "01", "Feb": "02", "Mar": "03", "Apr": "04",
    "May": "05", "Jun": "06", "Jul": "07", "Aug": "08",
    "Sep": "09", "Oct": "10", "Nov": "11", "Dec": "12"
}

_FILENAME_DATE_RE = re.compile(r"\d{4}[-_.]\d{2}[-_.]\d{2}")

def extract_date_from_filename(filepath: Path) -> str:
    """Finds date in filename quickly."""
    match = _FILENAME_DATE_RE.search(filepath.name)
    if match:
        return match.group().replace("_", "-").replace(".", "-")
    return ""

def build_timestamp(time_str: str, cached_date: str) -> str:
    """
    Parses various log timestamps into a single unified format: YYYY-MM-DD HH:MM:SS
    Bypasses datetime objects entirely using ultra-fast string slicing.
    """
    t = time_str.strip()
    if not t:
        return cached_date

    # --- FORMAT 1: ISO 8601 (e.g., "2026-01-19T07:33:23,289" or "2026-01-19 07:33:23") ---
    if t[0].isdigit() and len(t) >= 19 and (t[4] == "-" or t[4] == "_"):
        date_part = t[0:10].replace("_", "-")
        time_part = t[11:19]  # Strips away the 'T', milliseconds, and commas
        return f"{date_part} {time_part}"

    # --- FORMAT 2: Tomcat / Apache (e.g., "19-Jan-2026 06:48:33.088") ---
    # We detect it by checking if the 3rd character is a separator dash/slash
    if len(t) >= 20 and (t[2] == "-" or t[2] == "/"):
        day = t[0:2]
        month_str = t[3:6]
        month = _MONTH_TO_NUM.get(month_str, "01")
        year = t[7:11]
        time_part = t[12:20]  # Strips milliseconds (.088)
        return f"{year}-{month}-{day} {time_part}"

    # --- FORMAT 3: Localhost Requests (e.g., "15/Apr/2026:00:00:10") ---
    if len(t) >= 20 and t[11] == ":":
        day = t[0:2]
        month_str = t[3:6]
        month = _MONTH_TO_NUM.get(month_str, "01")
        year = t[7:11]
        time_part = t[12:20]
        return f"{year}-{month}-{day} {time_part}"

    # --- FORMAT 4: Bare Time Only (e.g., "06:48:33" or "06:48:33.088") ---
    # Fallback if the string is just the time chunk, use cached_date (assumed YYYY-MM-DD)
    time_part = t[0:8]
    return f"{cached_date} {time_part}"