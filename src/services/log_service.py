from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from core.analyzer import summarize_entries
from core.models import LogEntry
from core.parser import LobsterLogParser


@dataclass(slots=True)
class ParseLogsResult:
    entries: list[LogEntry]
    dataframe: pd.DataFrame
    summary: dict[str, object]
    files_processed: int
    pattern_profile: str


class LogService:
    """Orchestration service used by the GUI layer."""

    def __init__(self, pattern_config_path: Path):
        self.pattern_config_path = pattern_config_path
        self._pattern_config_cache: dict[str, object] | None = None

    def parse_folder(
        self,
        folder_path: Path,
        file_patterns: list[str] | None = None,
        pattern_profile: str | None = None,
        progress_callback=None,
    ) -> ParseLogsResult:
        files = self.discover_log_files(folder_path, file_patterns)
        active_profile, parser_patterns = self._resolve_parser_patterns(pattern_profile)
        parser = LobsterLogParser(parser_patterns)
        entries: list[LogEntry] = []

        if not files:
            self._emit_progress(progress_callback, 100)
            return ParseLogsResult(
                [], pd.DataFrame(), {"total_entries": 0}, 0, active_profile
            )

        for index, log_file in enumerate(files, start=1):
            entries.extend(parser.parse_file(log_file))
            progress_percent = int((index / len(files)) * 100)
            self._emit_progress(progress_callback, progress_percent)

        dataframe = self._to_dataframe(entries)
        summary = summarize_entries(entries)
        return ParseLogsResult(entries, dataframe, summary, len(files), active_profile)

    def discover_log_files(
        self, folder_path: Path, file_patterns: list[str] | None
    ) -> list[Path]:
        if not folder_path.exists() or not folder_path.is_dir():
            return []

        patterns = [
            pattern.strip() for pattern in file_patterns or ["*.log"] if pattern.strip()
        ]
        if not patterns:
            patterns = ["*.log"]

        files: list[Path] = []
        seen: set[Path] = set()
        for pattern in patterns:
            for file_path in sorted(folder_path.glob(pattern)):
                if file_path.is_file() and file_path not in seen:
                    files.append(file_path)
                    seen.add(file_path)
        return files

    def _load_patterns(self) -> dict[str, object]:
        if self._pattern_config_cache is not None:
            return self._pattern_config_cache

        with self.pattern_config_path.open("r", encoding="utf-8") as file_obj:
            self._pattern_config_cache = json.load(file_obj)
        return self._pattern_config_cache

    def _resolve_parser_patterns(
        self, pattern_profile: str | None
    ) -> tuple[str, dict[str, object]]:
        all_patterns = self._load_patterns()
        profiles_obj = all_patterns.get("profiles")
        base_patterns_obj = all_patterns.get("base_patterns")

        # Backward-compatible mode for old flat JSON.
        if not isinstance(profiles_obj, dict):
            return "default", all_patterns

        available_profiles = list(profiles_obj.keys())
        if not available_profiles:
            raise ValueError("Pattern configuration is missing profile definitions.")

        selected_profile = (pattern_profile or "").strip()
        if not selected_profile:
            default_profile = str(all_patterns.get("default_profile", "")).strip()
            selected_profile = default_profile or available_profiles[0]

        selected_patterns = profiles_obj.get(selected_profile)
        if not isinstance(selected_patterns, dict):
            raise ValueError(
                f"Unknown pattern profile '{selected_profile}'. Available: {', '.join(available_profiles)}"
            )

        resolved_patterns = self._merge_pattern_config(
            base_patterns_obj, selected_patterns
        )
        return selected_profile, resolved_patterns

    def _merge_pattern_config(
        self, base_patterns_obj: object, selected_patterns: dict[str, object]
    ) -> dict[str, object]:
        """Merge optional base patterns with profile-specific overrides."""
        if not isinstance(base_patterns_obj, dict):
            return dict(selected_patterns)

        merged: dict[str, object] = dict(base_patterns_obj)
        for key, value in selected_patterns.items():
            if (
                key in merged
                and isinstance(merged[key], dict)
                and isinstance(value, dict)
            ):
                nested = dict(merged[key])
                nested.update(value)
                merged[key] = nested
            else:
                merged[key] = value
        return merged

    def _to_dataframe(self, entries: list[LogEntry]) -> pd.DataFrame:
        rows = [
            {
                "Timestamp": entry.timestamp.isoformat(sep=" ")
                if entry.timestamp
                else "",
                "Level": entry.level,
                "Source": entry.source,
                "Component": entry.component,
                "ExceptionType": entry.exception_type,
                "Message": entry.message,
                "CausedBy": entry.caused_by,
                "Parameters": entry.parameters,
                "Profile": entry.profile or "",
                "FileName": entry.file_name,
            }
            for entry in entries
        ]
        return pd.DataFrame(rows)

    def _emit_progress(self, callback, value: int) -> None:
        if callback is None:
            return
        if hasattr(callback, "emit"):
            callback.emit(value)
        elif callable(callback):
            callback(value)
