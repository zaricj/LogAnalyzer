"""Forward Python ``logging`` records to the GUI via a Qt signal (thread-safe)."""

from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Signal


class LogBridge(QObject):
    """Owns the signal; emitting from any thread is queued to the GUI thread."""

    message = Signal(int, str)  # (levelno, formatted message)


class QtLogHandler(logging.Handler):
    def __init__(self, bridge: LogBridge, level: int = logging.INFO) -> None:
        super().__init__(level)
        self._bridge = bridge
        self.setFormatter(logging.Formatter("%(asctime)s  %(levelname)-7s  %(message)s", "%H:%M:%S"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._bridge.message.emit(record.levelno, self.format(record))
        except RuntimeError:
            # The bridge QObject was already destroyed (application shutting down).
            pass
