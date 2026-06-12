import re
from pathlib import Path
from datetime import datetime

_MONTH_MAP = {
    "Jan": "Jan", "Feb": "Feb", "Mar": "Mär", "Apr": "Apr",
    "May": "Mai", "Jun": "Jun", "Jul": "Jul", "Aug": "Aug",
    "Sep": "Sep", "Oct": "Okt", "Nov": "Nov", "Dec": "Dez"
}

_DATETIME_FORMATS = [
    "%d/%b/%Y:%H:%M:%S",       # 15/Apr/2026:00:00:10 (localhost https-request logs)
    "%d-%b-%Y %H:%M:%S.%f",   # 19-Jan-2026 06:48:33.088  (Tomcat SEVERE)
    "%d-%b-%Y %H:%M:%S",      # 19-Jan-2026 06:48:33
    "%Y-%m-%dT%H:%M:%S,%f",   # 2026-01-19T07:33:23,289   (ISO 8601, comma ms)
    "%Y-%m-%dT%H:%M:%S.%f",   # 2026-01-19T07:33:23.289   (ISO 8601, dot ms)
    "%Y-%m-%dT%H:%M:%S",      # 2026-01-19T07:33:23
    "%Y-%m-%d %H:%M:%S,%f",   # 2026-01-19 07:33:23,289
    "%Y-%m-%d %H:%M:%S.%f",   # 2026-01-19 07:33:23.289
    "%Y-%m-%d %H:%M:%S",      # 2026-01-19 07:33:23
]

# Patterns that represent a FULL datetime (date + time already present)
_FULL_DATETIME_PATTERNS = [
    # 19-Jan-2026 06:48:33.088
    re.compile(r"\d{1,2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}"),
    # 2026-01-19T07:33:23,289  or  2026-01-19 07:33:23
    re.compile(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}"),
    # 15/Apr/2026:06:15:40
    re.compile(r"\d{1,2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}")
    # Add more formats if needed
]

# Matches a bare time: 06:48:33 or 06:48:33.088 or 06:48:33,289
_TIME_ONLY_RE = re.compile(r"^\d{2}:\d{2}:\d{2}")
_FILENAME_DATE_RE = re.compile(r"\d{4}[-_.]\d{2}[-_.]\d{2}")


def is_full_datetime(time_str: str) -> bool:
    """Return True if the string already contains a date component."""
    return any(p.search(time_str) for p in _FULL_DATETIME_PATTERNS)


def extract_date_from_filename(filepath: Path) -> str:
    """Uses pre-compiled regex and avoids redundant Path ops."""
    match = _FILENAME_DATE_RE.search(filepath.name)
    if match:
        return match.group().replace("_", "-").replace(".", "-")
    return ""


def to_german_datetime(time_str: str) -> str:
    t = time_str.strip()
    for fmt in _DATETIME_FORMATS:
        try:
            dt = datetime.strptime(t, fmt)
            month_de = _MONTH_MAP.get(dt.strftime("%b"), dt.strftime("%b"))
            return dt.strftime(f"%d. {month_de} %Y %H:%M:%S")
        except ValueError:
            continue
    return t


def build_timestamp(time_str: str, cached_date: str) -> str:
    """
    Accepts a pre-calculated date string instead of a Path object
    to avoid per-row disk/string logic.
    """
    t = time_str.strip()
    if is_full_datetime(t):
        return to_german_datetime(t)  # Already complete, nothing to add
    
    # Check if t already looks like a full date (e.g. starts with 2026 or 15/)
    # if len(t) > 10 and (t[4] == "-" or t[2] == "/" or t[2] == "-"): 
    #     return to_german_datetime(t)

    if _TIME_ONLY_RE.match(t):
        return to_german_datetime(f"{cached_date} {t}")

    return to_german_datetime(f"{cached_date} {t}") if t else cached_date