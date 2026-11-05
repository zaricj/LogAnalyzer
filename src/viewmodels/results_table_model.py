"""Table model exposing the streamed result preview rows to a ``QTableView``."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import QAbstractTableModel, QModelIndex, QPersistentModelIndex, Qt

ModelIndex = QModelIndex | QPersistentModelIndex

# Cells longer than this are shortened in the grid; the tooltip shows the full text.
_MAX_DISPLAY_CHARS = 200


class ResultsTableModel(QAbstractTableModel):
    """Read-only table of extracted rows, keyed by the pattern's column headers."""

    def __init__(self, parent: Any = None) -> None:
        super().__init__(parent)
        self._headers: list[str] = []
        self._rows: list[list[str]] = []

    # ------------------------------------------------------------- mutation

    def reset(self, headers: list[str]) -> None:
        self.beginResetModel()
        self._headers = list(headers)
        self._rows = []
        self.endResetModel()

    def append_rows(self, rows: list[dict[str, str]]) -> None:
        if not rows:
            return
        if not self._headers:
            # Fallback: derive headers from the first row if none were provided.
            self.reset(list(rows[0].keys()))
        normalized = [[str(row.get(h, "") or "") for h in self._headers] for row in rows]
        first = len(self._rows)
        self.beginInsertRows(QModelIndex(), first, first + len(normalized) - 1)
        self._rows.extend(normalized)
        self.endInsertRows()

    # ---------------------------------------------------------- Qt overrides

    def rowCount(self, parent: ModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._rows)

    def columnCount(self, parent: ModelIndex = QModelIndex()) -> int:  # noqa: B008
        return 0 if parent.isValid() else len(self._headers)

    def data(self, index: ModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        value = self._rows[index.row()][index.column()]
        if role == Qt.ItemDataRole.DisplayRole:
            flat = " ".join(value.split())
            if len(flat) > _MAX_DISPLAY_CHARS:
                return flat[: _MAX_DISPLAY_CHARS - 1] + "…"
            return flat
        if role == Qt.ItemDataRole.ToolTipRole and len(value) > 40:
            return value
        return None

    def headerData(
        self,
        section: int,
        orientation: Qt.Orientation,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> Any:
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._headers[section] if 0 <= section < len(self._headers) else None
        return section + 1
