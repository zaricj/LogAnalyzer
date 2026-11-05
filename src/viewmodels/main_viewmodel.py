"""ViewModel for the main window: form state, validation, settings and job control."""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any

from PySide6.QtCore import QObject, QSettings, QThread, Signal, Slot

from src.models import (
    SearchConfig,
    SearchPhase,
    SearchProgress,
    SearchResult,
    SearchStatus,
)
from src.modules.core.parser import get_headers_from_patterns
from src.modules.io.regex_service import (
    compile_regex_patterns,
    load_patterns_json,
    validate_patterns_config,
)
from src.viewmodels.log_bridge import LogBridge, QtLogHandler
from src.viewmodels.results_table_model import ResultsTableModel
from src.viewmodels.search_worker import SearchWorker

logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_PATTERNS_CONFIG = PROJECT_ROOT / "patterns" / "patterns.json"
DEFAULT_OUTPUT_DIR = PROJECT_ROOT / "output"
PROGRESS_MAX = 1000

_SETTINGS_KEYS = (
    "patterns_config",
    "pattern_key",
    "files_directory",
    "file_pattern",
    "output_directory",
    "event_keyword",
    "export_excel",
)


class MainViewModel(QObject):
    # ---- form state (two-way binding) ----
    patterns_config_changed = Signal(str)
    pattern_keys_changed = Signal(list)
    pattern_key_changed = Signal(str)
    pattern_columns_changed = Signal(list)
    files_directory_changed = Signal(str)
    file_pattern_changed = Signal(str)
    output_directory_changed = Signal(str)
    event_keyword_changed = Signal(str)
    export_excel_changed = Signal(bool)

    # ---- derived / job state ----
    can_start_changed = Signal(bool)
    validation_message_changed = Signal(str)
    running_changed = Signal(bool)
    progress_changed = Signal(int)  # 0 .. PROGRESS_MAX
    progress_busy_changed = Signal(bool)  # indeterminate progress (preparing)
    status_text_changed = Signal(str)
    search_finished = Signal(object)  # SearchResult
    log_message = Signal(int, str)

    def __init__(self, settings: QSettings | None = None, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._settings = settings or QSettings("Glint", "Glint")

        self._patterns_config = str(DEFAULT_PATTERNS_CONFIG)
        self._patterns_json: dict[str, Any] = {}
        self._pattern_keys: list[str] = []
        self._pattern_key = ""
        self._pattern_columns: list[str] = []
        self._files_directory = ""
        self._file_pattern = "*.log"
        self._output_directory = str(DEFAULT_OUTPUT_DIR)
        self._event_keyword = ""
        self._export_excel = True

        self._can_start = False
        self._validation_message = ""
        self._running = False
        self._status_text = "Ready."
        self._last_result: SearchResult | None = None

        self._thread: QThread | None = None
        self._worker: SearchWorker | None = None

        self._results_model = ResultsTableModel(self)

        # Route log records of the whole application package into the GUI.
        self._log_bridge = LogBridge(self)
        self._log_bridge.message.connect(self.log_message)
        self._log_handler = QtLogHandler(self._log_bridge)
        app_logger = logging.getLogger("src")
        if app_logger.level == logging.NOTSET:
            # Don't inherit root's default WARNING level, the GUI log shows INFO.
            app_logger.setLevel(logging.INFO)
        app_logger.addHandler(self._log_handler)

        self._load_settings()
        self.reload_patterns()

    # ================================================================ getters

    @property
    def results_model(self) -> ResultsTableModel:
        return self._results_model

    @property
    def patterns_config(self) -> str:
        return self._patterns_config

    @property
    def pattern_keys(self) -> list[str]:
        return list(self._pattern_keys)

    @property
    def pattern_key(self) -> str:
        return self._pattern_key

    @property
    def pattern_columns(self) -> list[str]:
        return list(self._pattern_columns)

    @property
    def files_directory(self) -> str:
        return self._files_directory

    @property
    def file_pattern(self) -> str:
        return self._file_pattern

    @property
    def output_directory(self) -> str:
        return self._output_directory

    @property
    def event_keyword(self) -> str:
        return self._event_keyword

    @property
    def export_excel(self) -> bool:
        return self._export_excel

    @property
    def can_start(self) -> bool:
        return self._can_start

    @property
    def validation_message(self) -> str:
        return self._validation_message

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def status_text(self) -> str:
        return self._status_text

    @property
    def last_result(self) -> SearchResult | None:
        return self._last_result

    # ================================================================ setters

    @Slot(str)
    def set_patterns_config(self, value: str) -> None:
        value = value.strip()
        if value == self._patterns_config:
            return
        self._patterns_config = value
        self.patterns_config_changed.emit(value)
        self.reload_patterns()

    @Slot(str)
    def set_pattern_key(self, value: str) -> None:
        if value == self._pattern_key:
            return
        self._pattern_key = value
        self.pattern_key_changed.emit(value)
        self._update_pattern_columns()
        self._revalidate()

    @Slot(str)
    def set_files_directory(self, value: str) -> None:
        value = value.strip()
        if value == self._files_directory:
            return
        self._files_directory = value
        self.files_directory_changed.emit(value)
        self._revalidate()

    @Slot(str)
    def set_file_pattern(self, value: str) -> None:
        if value == self._file_pattern:
            return
        self._file_pattern = value
        self.file_pattern_changed.emit(value)
        self._revalidate()

    @Slot(str)
    def set_output_directory(self, value: str) -> None:
        value = value.strip()
        if value == self._output_directory:
            return
        self._output_directory = value
        self.output_directory_changed.emit(value)
        self._revalidate()

    @Slot(str)
    def set_event_keyword(self, value: str) -> None:
        if value == self._event_keyword:
            return
        self._event_keyword = value
        self.event_keyword_changed.emit(value)

    @Slot(bool)
    def set_export_excel(self, value: bool) -> None:
        if value == self._export_excel:
            return
        self._export_excel = value
        self.export_excel_changed.emit(value)

    # =============================================================== commands

    @Slot()
    def reload_patterns(self) -> None:
        """(Re)load the patterns JSON and refresh the available pattern keys."""
        self._patterns_json = {}
        path = Path(self._patterns_config) if self._patterns_config else None
        keys: list[str] = []

        if path is not None and path.is_file():
            try:
                data = load_patterns_json(path)
                validate_patterns_config(data)
                self._patterns_json = data
                keys = list(data.keys())
                logger.info("Loaded %d pattern(s) from %s", len(keys), path)
            except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
                logger.error("Invalid patterns config '%s': %s", path, exc)

        self._pattern_keys = keys
        self.pattern_keys_changed.emit(list(keys))

        if self._pattern_key not in keys:
            self.set_pattern_key(keys[0] if keys else "")
        else:
            self._update_pattern_columns()
        self._revalidate()

    @Slot()
    def start_search(self) -> None:
        if self._running:
            return
        config = self._build_config()
        errors = self._validation_errors()
        if errors:
            self._set_status(errors[0])
            return

        self._save_settings()
        self._last_result = None
        self._results_model.reset(self._pattern_columns)
        self.progress_changed.emit(0)
        self.progress_busy_changed.emit(True)
        self._set_status("Preparing search…")
        logger.info(
            "Starting search: pattern='%s', dir='%s', files='%s'%s",
            config.pattern_key,
            config.files_directory,
            config.file_pattern,
            f", keyword='{config.event_keyword}'" if config.event_keyword else "",
        )

        thread = QThread(self)
        worker = SearchWorker(config)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.progress.connect(self._on_progress)
        worker.rows_ready.connect(self._results_model.append_rows)
        worker.completed.connect(self._on_completed)
        worker.completed.connect(thread.quit)
        thread.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._on_thread_finished)

        self._thread, self._worker = thread, worker
        self._set_running(True)
        thread.start()

    @Slot()
    def cancel_search(self) -> None:
        if self._worker is not None and self._running:
            self._set_status("Cancelling…")
            self._worker.cancel()

    def shutdown(self, timeout_ms: int = 5000) -> None:
        """Cancel any running job and wait for the worker thread (call on app exit)."""
        if self._worker is not None:
            self._worker.cancel()
        if self._thread is not None:
            self._thread.quit()
            self._thread.wait(timeout_ms)
        logging.getLogger("src").removeHandler(self._log_handler)
        self._save_settings()

    # ============================================================ job signals

    @Slot(object)
    def _on_progress(self, progress: SearchProgress) -> None:
        if progress.phase is SearchPhase.PREPARING:
            self.progress_busy_changed.emit(True)
            self._set_status("Preparing search (indexing files)…")
            return

        self.progress_busy_changed.emit(False)
        self.progress_changed.emit(int(progress.fraction * PROGRESS_MAX))

        if progress.phase is SearchPhase.SEARCHING:
            self._set_status(
                f"Searching {progress.current_file} "
                f"({progress.file_index}/{progress.file_count}) — "
                f"{progress.units_done:,}/{progress.units_total:,} lines, "
                f"{progress.rows_found:,} matches"
            )
        else:
            self._set_status(
                f"Converting to Excel — {progress.units_done:,}/{progress.units_total:,} rows"
            )

    @Slot(object)
    def _on_completed(self, result: SearchResult) -> None:
        self._last_result = result
        self.progress_busy_changed.emit(False)
        elapsed = f"{result.elapsed_seconds:.2f}s"

        match result.status:
            case SearchStatus.COMPLETED:
                self.progress_changed.emit(PROGRESS_MAX)
                self._set_status(
                    f"Done in {elapsed}: {result.rows_written:,} rows from "
                    f"{result.files_searched} file(s)."
                )
                logger.info("CSV saved: %s", result.csv_path)
            case SearchStatus.NO_MATCHES:
                self.progress_changed.emit(PROGRESS_MAX)
                self._set_status(f"Finished in {elapsed}: no matches found.")
            case SearchStatus.CANCELLED:
                self.progress_changed.emit(0)
                self._set_status("Search cancelled.")
            case SearchStatus.FAILED:
                self.progress_changed.emit(0)
                self._set_status(f"Failed: {result.message}")

        self.search_finished.emit(result)

    @Slot()
    def _on_thread_finished(self) -> None:
        self._thread = None
        self._worker = None
        self._set_running(False)

    # ================================================================ helpers

    def _build_config(self) -> SearchConfig:
        return SearchConfig(
            patterns_config=Path(self._patterns_config),
            pattern_key=self._pattern_key,
            files_directory=Path(self._files_directory),
            file_pattern=self._file_pattern.strip(),
            output_directory=Path(self._output_directory),
            event_keyword=self._event_keyword.strip(),
            export_excel=self._export_excel,
        )

    def _update_pattern_columns(self) -> None:
        columns: list[str] = []
        category = self._patterns_json.get(self._pattern_key)
        if category:
            try:
                columns = get_headers_from_patterns(compile_regex_patterns(category))
            except re.error as exc:
                logger.error("Pattern '%s' does not compile: %s", self._pattern_key, exc)
        self._pattern_columns = columns
        self.pattern_columns_changed.emit(list(columns))

    def _validation_errors(self) -> list[str]:
        # Check raw strings first: Path("") silently becomes "." (the CWD).
        if not self._files_directory:
            return ["Select a log directory."]
        if not self._output_directory:
            return ["Select an output directory."]
        return self._build_config().validate()

    def _revalidate(self) -> None:
        errors = self._validation_errors()
        message = errors[0] if errors else ""
        can_start = not errors and not self._running

        if message != self._validation_message:
            self._validation_message = message
            self.validation_message_changed.emit(message)
        if can_start != self._can_start:
            self._can_start = can_start
            self.can_start_changed.emit(can_start)

    def _set_running(self, running: bool) -> None:
        if running == self._running:
            return
        self._running = running
        self.running_changed.emit(running)
        self._revalidate()

    def _set_status(self, text: str) -> None:
        if text != self._status_text:
            self._status_text = text
            self.status_text_changed.emit(text)

    def _load_settings(self) -> None:
        s = self._settings
        self._patterns_config = str(s.value("patterns_config", self._patterns_config))
        self._pattern_key = str(s.value("pattern_key", self._pattern_key))
        self._files_directory = str(s.value("files_directory", self._files_directory))
        self._file_pattern = str(s.value("file_pattern", self._file_pattern))
        self._output_directory = str(s.value("output_directory", self._output_directory))
        self._event_keyword = str(s.value("event_keyword", self._event_keyword))
        self._export_excel = s.value("export_excel", self._export_excel, type=bool)

    def _save_settings(self) -> None:
        for key in _SETTINGS_KEYS:
            self._settings.setValue(key, getattr(self, f"_{key}"))
        self._settings.sync()
