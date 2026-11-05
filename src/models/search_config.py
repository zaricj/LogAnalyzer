"""Pure data containers describing a search job, its progress and its outcome."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path

# An Excel sheet holds 1,048,576 rows; one of them is the header row.
EXCEL_MAX_DATA_ROWS = 1_048_575


@dataclass(frozen=True, slots=True)
class SearchConfig:
    """Immutable description of one search pipeline run."""

    patterns_config: Path
    pattern_key: str
    files_directory: Path
    file_pattern: str
    output_directory: Path
    event_keyword: str = ""
    export_excel: bool = True

    def output_csv(self, now: datetime | None = None) -> Path:
        """Build the CSV output path: ``<output_dir>/<YYYY_MM_DD>_<pattern_key>.csv``."""
        prefix = (now or datetime.now()).strftime("%Y_%m_%d")
        return self.output_directory / f"{prefix}_{self.pattern_key}.csv"

    def validate(self) -> list[str]:
        """Return human readable validation errors (empty list when valid)."""
        errors: list[str] = []
        if not self.patterns_config.is_file():
            errors.append(f"Patterns config not found: {self.patterns_config}")
        if not self.pattern_key:
            errors.append("No pattern key selected.")
        if not self.files_directory.is_dir():
            errors.append(f"Log directory not found: {self.files_directory}")
        if not self.file_pattern.strip():
            errors.append("File pattern must not be empty.")
        if self.output_directory.exists() and not self.output_directory.is_dir():
            errors.append(f"Output path is not a directory: {self.output_directory}")
        return errors


class SearchPhase(Enum):
    PREPARING = auto()
    SEARCHING = auto()
    EXPORTING_EXCEL = auto()


@dataclass(frozen=True, slots=True)
class SearchProgress:
    """Snapshot of a running search, emitted periodically by the engine."""

    phase: SearchPhase
    current_file: str = ""
    file_index: int = 0
    file_count: int = 0
    units_done: int = 0
    units_total: int = 0
    rows_found: int = 0

    @property
    def fraction(self) -> float:
        """Progress of the current phase in the range ``0.0 .. 1.0``."""
        if self.units_total <= 0:
            return 0.0
        return min(1.0, self.units_done / self.units_total)


class SearchStatus(Enum):
    COMPLETED = auto()
    NO_MATCHES = auto()
    CANCELLED = auto()
    FAILED = auto()


@dataclass(slots=True)
class SearchResult:
    """Final outcome of a search pipeline run."""

    status: SearchStatus
    rows_written: int = 0
    files_searched: int = 0
    csv_path: Path | None = None
    excel_path: Path | None = None
    elapsed_seconds: float = 0.0
    headers: list[str] = field(default_factory=list)
    message: str = ""
