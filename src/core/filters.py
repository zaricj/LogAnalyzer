from __future__ import annotations

from datetime import datetime
from typing import Iterable, Iterator

from core.models import LogEntry


def filter_by_level(
    entries: Iterable[LogEntry], levels: set[str]
) -> Iterator[LogEntry]:
    normalized = {level.upper() for level in levels}
    for entry in entries:
        if entry.level.upper() in normalized:
            yield entry


def filter_by_component(
    entries: Iterable[LogEntry], components: set[str]
) -> Iterator[LogEntry]:
    normalized = {component.lower() for component in components}
    for entry in entries:
        if entry.component.lower() in normalized:
            yield entry


def filter_by_date_range(
    entries: Iterable[LogEntry],
    start_date: datetime | None,
    end_date: datetime | None,
) -> Iterator[LogEntry]:
    for entry in entries:
        if entry.timestamp is None:
            continue
        if start_date and entry.timestamp < start_date:
            continue
        if end_date and entry.timestamp > end_date:
            continue
        yield entry
