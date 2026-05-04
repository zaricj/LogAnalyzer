from __future__ import annotations

from collections import Counter
from typing import Iterable

from core.models import LogEntry


def summarize_entries(entries: Iterable[LogEntry]) -> dict[str, object]:
    """Create high-level counters used by the GUI summary output."""
    entry_list = list(entries)
    exception_counter = Counter(entry.exception_type for entry in entry_list)
    component_counter = Counter(entry.component for entry in entry_list)
    profile_counter = Counter(entry.profile for entry in entry_list if entry.profile)

    return {
        "total_entries": len(entry_list),
        "exceptions": dict(exception_counter),
        "components": dict(component_counter),
        "profiles": dict(profile_counter),
    }
