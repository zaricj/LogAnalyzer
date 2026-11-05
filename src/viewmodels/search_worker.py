"""Background worker that runs the ``PipelineEngine`` inside a ``QThread``."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal, Slot

from src.models import (
    CancellationToken,
    PipelineEngine,
    SearchConfig,
    SearchProgress,
    SearchResult,
    SearchStatus,
)

logger = logging.getLogger(__name__)


class SearchWorker(QObject):
    """Worker object meant to be moved to a ``QThread``.

    All signals are emitted from the worker thread; Qt queues them to the
    receivers living on the GUI thread automatically.
    """

    progress = Signal(object)  # SearchProgress
    rows_ready = Signal(list)  # list[dict[str, str]]
    completed = Signal(object)  # SearchResult

    def __init__(self, config: SearchConfig, engine: PipelineEngine | None = None) -> None:
        super().__init__()
        self._config = config
        self._engine = engine or PipelineEngine()
        self._token = CancellationToken()

    def cancel(self) -> None:
        """Request cancellation. Safe to call directly from any thread."""
        self._token.cancel()

    @Slot()
    def run(self) -> None:
        try:
            result = self._engine.run(
                self._config,
                token=self._token,
                on_progress=self._emit_progress,
                on_rows=self.rows_ready.emit,
            )
        except Exception as exc:  # noqa: BLE001 - never let the thread die silently
            logger.exception("Search worker crashed")
            result = SearchResult(status=SearchStatus.FAILED, message=str(exc))
        self.completed.emit(result)

    def _emit_progress(self, progress: SearchProgress) -> None:
        self.progress.emit(progress)
