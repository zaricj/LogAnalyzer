from dataclasses import dataclass
from datetime import datetime


@dataclass(slots=True)
class LogEntry:
    """Normalized log entry produced by the parser."""

    timestamp: datetime | None
    level: str
    source: str
    component: str
    message: str
    exception_type: str
    sql_statement: str = ""
    parameters: str = ""
    caused_by: str = ""
    profile: str | None = None
    raw: str = ""
    file_name: str = ""
