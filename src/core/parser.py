from __future__ import annotations

import re
from datetime import date, datetime
from pathlib import Path
from typing import Iterator, Mapping

from core.models import LogEntry


class LobsterLogParser:
    """Parses Lobster error/system log files into normalized entries."""

    _FILE_DATE_PATTERN = re.compile(r"(?P<year>\d{4})_(?P<month>\d{2})_(?P<day>\d{2})")

    def __init__(self, pattern_config: Mapping[str, object]):
        entry_pattern_text = str(pattern_config.get("entry_header_pattern", "")).strip()
        if not entry_pattern_text:
            raise ValueError("Missing required pattern: entry_header_pattern")

        exception_patterns = pattern_config.get("exception_patterns", {})

        self.exception_patterns = {
            name: re.compile(pattern, re.MULTILINE | re.DOTALL)
            for name, pattern in exception_patterns.items()
        }

        self.entry_header_pattern = re.compile(entry_pattern_text, re.DOTALL)

        profile_header_pattern = str(
            pattern_config.get("profile_header_pattern", "")
        ).strip()
        self.profile_header_pattern = (
            re.compile(profile_header_pattern, re.IGNORECASE)
            if profile_header_pattern
            else None
        )

        self.sql_statement_pattern = self._compile_optional_pattern(
            str(pattern_config.get("sql_statement_pattern", "")).strip(),
            re.DOTALL,
        )
        self.param_pattern = self._compile_optional_pattern(
            str(pattern_config.get("param_pattern", "")).strip()
        )
        self.caused_by_pattern = self._compile_optional_pattern(
            str(pattern_config.get("caused_by_pattern", "")).strip(),
            re.MULTILINE,
        )
        self.ignore_stacktrace_pattern = self._compile_optional_pattern(
            str(pattern_config.get("ignore_stacktrace_pattern", "")).strip(),
            re.MULTILINE,
        )

    def parse_file(self, file_path: Path) -> Iterator[LogEntry]:
        """Yield parsed log entries for a single log file."""
        log_data = file_path.read_text(encoding="utf-8", errors="ignore")
        profile = self._extract_profile(log_data)
        log_date = self._extract_date_from_filename(file_path)

        for match in self.entry_header_pattern.finditer(log_data):
            time_part = match.group("time").strip()
            source = match.group("source").strip()
            raw_block = match.group("error_block").strip()
            cleaned_block = self._clean_error_block(raw_block)

            sql_statement = self._extract_sql(cleaned_block)
            exception_type = self._detect_exception_type(cleaned_block)
            parameters = self._extract_parameters(cleaned_block)
            caused_by = self._extract_caused_by(cleaned_block)
            message = self._extract_summary(cleaned_block, sql_statement)
            component = self._extract_component(source)
            level = self._extract_level(source)

            yield LogEntry(
                timestamp=self._build_timestamp(log_date, time_part),
                level=level,
                source=source,
                component=component,
                message=message,
                exception_type=exception_type,
                sql_statement=sql_statement,
                parameters=parameters,
                caused_by=caused_by,
                profile=profile,
                raw=raw_block,
                file_name=file_path.name,
            )

    def _compile_optional_pattern(self, pattern_text: str, flags: int = 0):
        if not pattern_text:
            return None
        return re.compile(pattern_text, flags)

    def _extract_profile(self, log_data: str) -> str | None:
        if not self.profile_header_pattern:
            return None
        profile_match = self.profile_header_pattern.search(log_data)
        if not profile_match:
            return None
        if "profile" not in profile_match.groupdict():
            return None
        return profile_match.group("profile")

    def _extract_date_from_filename(self, file_path: Path) -> date | None:
        date_match = self._FILE_DATE_PATTERN.search(file_path.stem)
        if not date_match:
            return None

        try:
            return date(
                year=int(date_match.group("year")),
                month=int(date_match.group("month")),
                day=int(date_match.group("day")),
            )
        except ValueError:
            return None

    def _build_timestamp(
        self, log_date: date | None, time_part: str
    ) -> datetime | None:
        if log_date is None:
            return None
        try:
            parsed_time = datetime.strptime(time_part, "%H:%M:%S").time()
        except ValueError:
            return None
        return datetime.combine(log_date, parsed_time)

    def _clean_error_block(self, block: str) -> str:
        cleaned = block
        if self.ignore_stacktrace_pattern:
            cleaned = self.ignore_stacktrace_pattern.sub("", cleaned)
        cleaned = re.sub(r"\n{2,}", "\n", cleaned)
        return cleaned.strip()

    def _extract_sql(self, block: str) -> str:
        if not self.sql_statement_pattern:
            return ""
        sql_match = self.sql_statement_pattern.search(block)
        if not sql_match:
            return ""
        return sql_match.group("sql").strip()

    def _extract_parameters(self, block: str) -> str:
        if not self.param_pattern:
            return ""
        params = self.param_pattern.findall(block)
        if not params:
            return ""
        return "; ".join(f"{param}='{value}'" for param, value in params)

    def _extract_caused_by(self, block: str) -> str:
        if not self.caused_by_pattern:
            return ""
        caused_match = self.caused_by_pattern.search(block)
        if not caused_match:
            return ""
        return caused_match.group("cause").strip()

    def _detect_exception_type(self, block: str) -> str:
        for key, regex in self.exception_patterns.items():
            if regex.search(block):
                return key
        return "unknown_exception"

    def _extract_summary(self, block: str, sql_statement: str) -> str:
        if sql_statement:
            return sql_statement
        if not block:
            return ""
        return block.splitlines()[0].strip()

    def _extract_level(self, source: str) -> str:
        if ":" not in source:
            return "UNKNOWN"
        return source.split(":", 1)[0].strip().upper()

    def _extract_component(self, source: str) -> str:
        parts = [part for part in source.split(":") if part]
        if not parts:
            return source
        return parts[-1].strip()
