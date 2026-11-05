"""GUI-agnostic search pipeline with progress callbacks and cooperative cancellation.

This module must never import Qt widgets: it is shared by any front-end
(Qt GUI, tests, scripts) and only talks through plain callbacks.
"""

from __future__ import annotations

import logging
import re
import threading
import time
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

from src.models.search_config import (
    EXCEL_MAX_DATA_ROWS,
    SearchConfig,
    SearchPhase,
    SearchProgress,
    SearchResult,
    SearchStatus,
)
from src.modules.core.parser import get_headers_from_patterns, iter_rows_from_files
from src.modules.io.exporters import write_csv, write_excel_from_csv
from src.modules.io.file_utils import get_file_info, get_files_in_folder
from src.modules.io.regex_service import load_pattern_search_rule
from src.modules.utility.thread_executor import run_with_threading

logger = logging.getLogger(__name__)

Row = dict[str, str]
ProgressCallback = Callable[[SearchProgress], None]
RowBatchCallback = Callable[[list[Row]], None]


class PipelineCancelled(Exception):
    """Raised inside the pipeline when the cancellation token has been triggered."""


class CancellationToken:
    """Thread-safe cancellation flag shared between a controller and a worker."""

    __slots__ = ("_event",)

    def __init__(self) -> None:
        self._event = threading.Event()

    def cancel(self) -> None:
        self._event.set()

    @property
    def is_cancelled(self) -> bool:
        return self._event.is_set()

    def raise_if_cancelled(self) -> None:
        if self._event.is_set():
            raise PipelineCancelled()


class _ProgressReporter:
    """Accumulates progress counters and throttles callback invocations."""

    def __init__(
        self,
        callback: ProgressCallback | None,
        token: CancellationToken,
        interval: float,
    ) -> None:
        self._callback = callback
        self._token = token
        self._interval = interval
        self._last_emit = 0.0
        self.phase = SearchPhase.PREPARING
        self.current_file = ""
        self.file_index = 0
        self.file_count = 0
        self.units_done = 0
        self.units_total = 0
        self.rows_found = 0

    def advance(self, units: int) -> None:
        self._token.raise_if_cancelled()
        self.units_done += units
        self.emit()

    def emit(self, force: bool = False) -> None:
        if self._callback is None:
            return
        now = time.monotonic()
        if not force and now - self._last_emit < self._interval:
            return
        self._last_emit = now
        self._callback(
            SearchProgress(
                phase=self.phase,
                current_file=self.current_file,
                file_index=self.file_index,
                file_count=self.file_count,
                units_done=self.units_done,
                units_total=self.units_total,
                rows_found=self.rows_found,
            )
        )


class PipelineEngine:
    """Runs search → CSV → (optional) Excel for a ``SearchConfig``.

    The engine is synchronous; callers are responsible for running it on a
    background thread. Callbacks are invoked on that same thread.
    """

    def __init__(
        self,
        *,
        progress_interval: float = 0.05,
        preview_limit: int = 1000,
        preview_batch_size: int = 100,
    ) -> None:
        self._progress_interval = progress_interval
        self._preview_limit = preview_limit
        self._preview_batch_size = preview_batch_size

    def run(
        self,
        config: SearchConfig,
        token: CancellationToken | None = None,
        on_progress: ProgressCallback | None = None,
        on_rows: RowBatchCallback | None = None,
    ) -> SearchResult:
        """Execute the pipeline. Never raises: failures are reported in the result."""
        token = token or CancellationToken()
        reporter = _ProgressReporter(on_progress, token, self._progress_interval)
        started = time.perf_counter()
        result = SearchResult(status=SearchStatus.FAILED)

        try:
            self._run(config, token, reporter, on_rows, result)
        except PipelineCancelled:
            logger.warning("Search cancelled by user.")
            self._discard_outputs(result)
            result.rows_written = 0
            result.status = SearchStatus.CANCELLED
            result.message = "Search cancelled."
        except (OSError, ValueError, TypeError, re.error, UnicodeDecodeError) as exc:
            logger.error("Search failed: %s", exc)
            result.status = SearchStatus.FAILED
            result.message = str(exc)
        except Exception as exc:  # noqa: BLE001 - boundary of a background job
            logger.exception("Unexpected error during search")
            result.status = SearchStatus.FAILED
            result.message = f"Unexpected error: {exc}"
        finally:
            result.elapsed_seconds = time.perf_counter() - started

        return result

    # ------------------------------------------------------------------ steps

    def _run(
        self,
        config: SearchConfig,
        token: CancellationToken,
        reporter: _ProgressReporter,
        on_rows: RowBatchCallback | None,
        result: SearchResult,
    ) -> None:
        reporter.emit(force=True)

        files = get_files_in_folder(config.files_directory, config.file_pattern)
        if not files:
            raise FileNotFoundError(
                f"No files found in '{config.files_directory}' matching '{config.file_pattern}'."
            )
        logger.info("Found %d file(s) matching '%s'.", len(files), config.file_pattern)

        compiled, separator_regex = load_pattern_search_rule(
            config.patterns_config, config.pattern_key
        )
        result.headers = get_headers_from_patterns(compiled)
        token.raise_if_cancelled()

        files_info = [info for info in run_with_threading(get_file_info, files) if info]
        token.raise_if_cancelled()
        if not files_info:
            raise OSError("None of the matching files could be read.")
        result.files_searched = len(files_info)

        reporter.phase = SearchPhase.SEARCHING
        reporter.file_count = len(files_info)
        reporter.units_total = sum(int(info["Lines"]) for info in files_info)

        def on_file_start(index: int, info: dict[str, Any]) -> None:
            token.raise_if_cancelled()
            reporter.file_index = index + 1
            reporter.current_file = Path(info["Filepath"]).name
            logger.info("Searching %s (%s lines)…", reporter.current_file, f"{info['Lines']:,}")
            reporter.emit(force=True)

        rows = iter_rows_from_files(
            files_info,
            separator_regex,
            compiled,
            config.event_keyword,
            on_file_start=on_file_start,
            on_lines=reporter.advance,
        )

        csv_path = config.output_csv()
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        result.csv_path = csv_path

        count = write_csv(
            csv_path,
            result.headers,
            self._observe_rows(rows, token, reporter, on_rows),
        )
        result.rows_written = count
        reporter.emit(force=True)

        if count == 0:
            self._discard_outputs(result)
            result.status = SearchStatus.NO_MATCHES
            result.message = "No matches were found, nothing was written."
            logger.warning(result.message)
            return

        logger.info("Wrote %s rows to %s", f"{count:,}", csv_path)

        if config.export_excel:
            self._export_excel(csv_path, count, token, reporter, result)

        result.status = SearchStatus.COMPLETED
        result.message = f"Wrote {count:,} rows."

    def _observe_rows(
        self,
        rows: Iterator[Row],
        token: CancellationToken,
        reporter: _ProgressReporter,
        on_rows: RowBatchCallback | None,
    ) -> Iterator[Row]:
        """Pass rows through while counting them and streaming a preview batch-wise."""
        batch: list[Row] = []
        previewed = 0

        for row in rows:
            token.raise_if_cancelled()
            reporter.rows_found += 1

            if on_rows is not None and previewed < self._preview_limit:
                batch.append(row)
                previewed += 1
                if len(batch) >= self._preview_batch_size or previewed == self._preview_limit:
                    on_rows(batch)
                    batch = []

            yield row

        if on_rows is not None and batch:
            on_rows(batch)

    def _export_excel(
        self,
        csv_path: Path,
        count: int,
        token: CancellationToken,
        reporter: _ProgressReporter,
        result: SearchResult,
    ) -> None:
        if count > EXCEL_MAX_DATA_ROWS:
            logger.warning(
                "CSV has %s rows and exceeds Excel's row limit; skipping Excel export.",
                f"{count:,}",
            )
            return

        excel_path = csv_path.with_suffix(".xlsx")
        result.excel_path = excel_path
        reporter.phase = SearchPhase.EXPORTING_EXCEL
        reporter.units_done = 0
        reporter.units_total = count
        reporter.emit(force=True)
        logger.info("Converting CSV to Excel…")

        write_excel_from_csv(csv_path, excel_path, on_rows=reporter.advance)
        reporter.emit(force=True)
        logger.info("Excel saved to %s", excel_path)

    @staticmethod
    def _discard_outputs(result: SearchResult) -> None:
        """Remove partially written output files and clear their paths."""
        for attr in ("csv_path", "excel_path"):
            path: Path | None = getattr(result, attr)
            if path is None:
                continue
            try:
                path.unlink(missing_ok=True)
            except OSError as exc:
                logger.warning("Could not remove partial output %s: %s", path, exc)
            setattr(result, attr, None)
