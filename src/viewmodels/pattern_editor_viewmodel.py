"""ViewModel for the pattern config editor: working copy, validation, save/revert.

The editor never touches the file until ``save()`` is called. It edits a
``PatternConfig`` working copy, re-validates after every change (compiling a
handful of regexes is cheap enough to do per keystroke) and compares against
the last saved snapshot to track unsaved changes.
"""

from __future__ import annotations

import json
import logging
import re
from enum import Enum, auto
from pathlib import Path
from typing import Any

from PySide6.QtCore import (
    QAbstractListModel,
    QAbstractTableModel,
    QModelIndex,
    QObject,
    QPersistentModelIndex,
    Qt,
    Signal,
    Slot,
)

from src.models.pattern_config import (
    SEPARATOR_KEY,
    IssueField,
    PatternCategory,
    PatternConfig,
    PatternRule,
    ValidationIssue,
)
from src.modules.core.parser import get_headers_from_patterns
from src.modules.io.regex_service import PATTERN_FLAGS, load_patterns_json, save_patterns_json

logger = logging.getLogger(__name__)

ModelIndex = QModelIndex | QPersistentModelIndex

# Custom role: the first validation message of an item (``str``) or ``None``.
IssueRole = Qt.ItemDataRole.UserRole + 1


class SaveOutcome(Enum):
    SAVED = auto()
    INVALID = auto()  # validation errors, nothing written
    CONFLICT = auto()  # file changed on disk since it was loaded, nothing written
    FAILED = auto()  # I/O or serialisation error, see ``error_occurred``


# ======================================================== item models


class CategoryListModel(QAbstractListModel):
    """Editable list of category names, backed by the editor's working copy."""

    def __init__(self, editor: PatternEditorViewModel) -> None:
        super().__init__(editor)
        self._editor = editor
        self._issues: dict[int, str] = {}

    def rowCount(self, parent: ModelIndex = QModelIndex()) -> int:  # noqa: N802 - Qt override
        return 0 if parent.isValid() else len(self._editor.config.categories)

    def data(self, index: ModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        category = self._editor.config.categories[index.row()]
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return category.name
        if role in (Qt.ItemDataRole.ToolTipRole, IssueRole):
            return self._issues.get(index.row())
        return None

    def flags(self, index: ModelIndex) -> Qt.ItemFlag:
        base = super().flags(index)
        return base | Qt.ItemFlag.ItemIsEditable if index.isValid() else base

    def setData(self, index: ModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        return self._editor.rename_category(index.row(), str(value))

    # -- mutation helpers used by the editor (keep begin/end pairs in one place)

    def _reset(self) -> None:
        self.beginResetModel()
        self.endResetModel()

    def _insert(self, row: int, category: PatternCategory) -> None:
        self.beginInsertRows(QModelIndex(), row, row)
        self._editor.config.categories.insert(row, category)
        self.endInsertRows()

    def _remove(self, row: int) -> None:
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._editor.config.categories[row]
        self.endRemoveRows()

    def _row_changed(self, row: int) -> None:
        index = self.index(row)
        self.dataChanged.emit(index, index)

    def _set_issues(self, issues: dict[int, str]) -> None:
        if issues == self._issues:
            return
        self._issues = issues
        if self.rowCount():
            roles = [Qt.ItemDataRole.ToolTipRole, IssueRole]
            self.dataChanged.emit(self.index(0), self.index(self.rowCount() - 1), roles)


class PatternTableModel(QAbstractTableModel):
    """Editable ``Name | Regex`` table of the editor's current category."""

    NAME_COLUMN, REGEX_COLUMN = 0, 1
    _HEADERS = ("Name", "Regex")
    _FIELDS = (IssueField.NAME, IssueField.REGEX)

    def __init__(self, editor: PatternEditorViewModel) -> None:
        super().__init__(editor)
        self._editor = editor
        self._issues: dict[tuple[int, IssueField], str] = {}

    @property
    def _rules(self) -> list[PatternRule]:
        category = self._editor.current_category_data
        return category.rules if category is not None else []

    def rowCount(self, parent: ModelIndex = QModelIndex()) -> int:  # noqa: N802 - Qt override
        return 0 if parent.isValid() else len(self._rules)

    def columnCount(self, parent: ModelIndex = QModelIndex()) -> int:  # noqa: N802 - Qt override
        return 0 if parent.isValid() else len(self._HEADERS)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.ItemDataRole.DisplayRole) -> Any:  # noqa: N802
        if role != Qt.ItemDataRole.DisplayRole:
            return None
        if orientation == Qt.Orientation.Horizontal:
            return self._HEADERS[section]
        return str(section + 1)

    def data(self, index: ModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None
        rule = self._rules[index.row()]
        column = index.column()
        if role in (Qt.ItemDataRole.DisplayRole, Qt.ItemDataRole.EditRole):
            return rule.name if column == self.NAME_COLUMN else rule.regex
        if role in (Qt.ItemDataRole.ToolTipRole, IssueRole):
            issue = self._issues.get((index.row(), self._FIELDS[column]))
            if issue is None and role == Qt.ItemDataRole.ToolTipRole and column == self.REGEX_COLUMN:
                return rule.regex  # long regexes are elided in the grid
            return issue
        return None

    def flags(self, index: ModelIndex) -> Qt.ItemFlag:
        base = super().flags(index)
        return base | Qt.ItemFlag.ItemIsEditable if index.isValid() else base

    def setData(self, index: ModelIndex, value: Any, role: int = Qt.ItemDataRole.EditRole) -> bool:  # noqa: N802
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False
        if index.column() == self.NAME_COLUMN:
            return self._editor.rename_pattern(index.row(), str(value))
        return self._editor.set_pattern_regex(index.row(), str(value))

    # -- mutation helpers used by the editor

    def _reset(self) -> None:
        self.beginResetModel()
        self._issues = {}
        self.endResetModel()

    def _insert(self, row: int, rule: PatternRule) -> None:
        self.beginInsertRows(QModelIndex(), row, row)
        self._rules.insert(row, rule)
        self.endInsertRows()

    def _remove(self, row: int) -> None:
        self.beginRemoveRows(QModelIndex(), row, row)
        del self._rules[row]
        self.endRemoveRows()

    def _move(self, row: int, target: int) -> None:
        # Qt's destination is the row the item is inserted *before*.
        destination = target + 1 if target > row else target
        self.beginMoveRows(QModelIndex(), row, row, QModelIndex(), destination)
        rules = self._rules
        rules.insert(target, rules.pop(row))
        self.endMoveRows()

    def _cell_changed(self, row: int, column: int) -> None:
        index = self.index(row, column)
        self.dataChanged.emit(index, index)

    def _set_issues(self, issues: dict[tuple[int, IssueField], str]) -> None:
        if issues == self._issues:
            return
        self._issues = issues
        if self.rowCount():
            roles = [Qt.ItemDataRole.ToolTipRole, IssueRole]
            last = self.index(self.rowCount() - 1, self.columnCount() - 1)
            self.dataChanged.emit(self.index(0, 0), last, roles)


# ========================================================== viewmodel


class PatternEditorViewModel(QObject):
    current_category_changed = Signal(int)  # row, -1 when none
    separator_changed = Signal(str)
    columns_changed = Signal(list)
    issues_changed = Signal()  # re-query separator_issue / category_issue / pattern_issue / summary
    dirty_changed = Signal(bool)
    can_save_changed = Signal(bool)
    saved = Signal(str)  # path of the written file
    error_occurred = Signal(str)

    def __init__(self, path: Path, initial_category: str = "", parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._path = path
        self._config = PatternConfig()
        self._saved = PatternConfig()
        self._mtime_ns: int | None = None
        self._load_error = ""
        self._is_new_file = False

        self._current = -1
        self._issues: list[ValidationIssue] = []
        self._columns: list[str] = []
        self._dirty = False
        self._can_save = False

        self._categories_model = CategoryListModel(self)
        self._patterns_model = PatternTableModel(self)

        self._load()
        names = [c.name for c in self._config.categories]
        self.select_category(names.index(initial_category) if initial_category in names else 0)
        self._revalidate()

    # ================================================================ getters

    @property
    def path(self) -> Path:
        return self._path

    @property
    def load_error(self) -> str:
        """Non-empty when the file exists but could not be parsed (editor is unusable)."""
        return self._load_error

    @property
    def is_new_file(self) -> bool:
        return self._is_new_file

    @property
    def config(self) -> PatternConfig:
        return self._config

    @property
    def categories_model(self) -> CategoryListModel:
        return self._categories_model

    @property
    def patterns_model(self) -> PatternTableModel:
        return self._patterns_model

    @property
    def current_category(self) -> int:
        return self._current

    @property
    def current_category_data(self) -> PatternCategory | None:
        if 0 <= self._current < len(self._config.categories):
            return self._config.categories[self._current]
        return None

    @property
    def separator(self) -> str:
        category = self.current_category_data
        return category.separator if category is not None else ""

    @property
    def columns(self) -> list[str]:
        return list(self._columns)

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    @property
    def can_save(self) -> bool:
        return self._can_save

    @property
    def issue_count(self) -> int:
        return len(self._issues)

    def separator_issue(self) -> str:
        return self._first_issue(self._current, None, IssueField.SEPARATOR)

    def category_issue(self) -> str:
        """Category-level problem of the current category other than name/separator."""
        return self._first_issue(self._current, None, IssueField.CATEGORY)

    def pattern_issue(self, row: int) -> str:
        """All problems of one pattern of the current category, one per line."""
        return "\n".join(
            i.message for i in self._issues if i.category == self._current and i.rule == row
        )

    def pattern_regex(self, row: int) -> str:
        category = self.current_category_data
        if category is None or not 0 <= row < len(category.rules):
            return ""
        return category.rules[row].regex

    def summary(self) -> str:
        """One line describing the editor state for the footer."""
        if self._issues:
            first = self._issues[0]
            where = self._issue_location(first)
            more = f" (+{len(self._issues) - 1} more)" if len(self._issues) > 1 else ""
            return f"{where}: {first.message}{more}"
        count = len(self._config.categories)
        rules = sum(len(c.rules) for c in self._config.categories)
        state = "Unsaved changes" if self._dirty else ("New file" if self._is_new_file else "Saved")
        return f"{state} · {count} categor{'y' if count == 1 else 'ies'}, {rules} pattern(s)"

    # =============================================================== commands

    @Slot(int)
    def select_category(self, row: int) -> None:
        self._select(row)

    def _select(self, row: int, force: bool = False) -> None:
        if not 0 <= row < len(self._config.categories):
            row = -1
        if row == self._current and not force:
            return
        self._current = row
        self._patterns_model._reset()
        self._refresh_issue_views()
        self._update_columns()
        self.current_category_changed.emit(row)
        self.separator_changed.emit(self.separator)

    @Slot(result=int)
    def add_category(self) -> int:
        row = self._current + 1 if self._current >= 0 else len(self._config.categories)
        category = PatternCategory(
            name=self._config.unique_category_name(),
            separator=r"^(?P<time>\d{2}:\d{2}:\d{2})",
            rules=[PatternRule("default", "")],
        )
        self._categories_model._insert(row, category)
        if self._current >= row:
            self._current += 1  # keep the index pointing at the same category
        self.select_category(row)
        self._after_edit()
        return row

    @Slot(int)
    def remove_category(self, row: int) -> None:
        if not 0 <= row < len(self._config.categories):
            return
        self._current = -1  # detach the table before its backing list disappears
        self._patterns_model._reset()
        self._categories_model._remove(row)
        self._select(min(row, len(self._config.categories) - 1), force=True)
        self._after_edit()

    def rename_category(self, row: int, name: str) -> bool:
        category = self._config.categories[row]
        if name == category.name:
            return False
        category.name = name
        self._categories_model._row_changed(row)
        self._after_edit()
        return True

    @Slot(str)
    def set_separator(self, value: str) -> None:
        category = self.current_category_data
        if category is None or value == category.separator:
            return
        category.separator = value
        self.separator_changed.emit(value)
        self._after_edit()

    def add_pattern(self, after_row: int = -1) -> int:
        """Insert a new pattern below ``after_row`` (or at the end); return its row."""
        category = self.current_category_data
        if category is None:
            return -1
        row = after_row + 1 if 0 <= after_row < len(category.rules) else len(category.rules)
        self._patterns_model._insert(row, PatternRule(category.unique_rule_name(), ""))
        self._after_edit()
        return row

    @Slot(int)
    def remove_pattern(self, row: int) -> None:
        category = self.current_category_data
        if category is None or not 0 <= row < len(category.rules):
            return
        self._patterns_model._remove(row)
        self._after_edit()

    def move_pattern(self, row: int, delta: int) -> int:
        """Move a pattern up (``-1``) or down (``+1``); return its new row.

        Order matters: for each column the first pattern with a non-empty
        match wins.
        """
        category = self.current_category_data
        if category is None or not 0 <= row < len(category.rules):
            return row
        target = row + delta
        if not 0 <= target < len(category.rules) or target == row:
            return row
        self._patterns_model._move(row, target)
        self._after_edit()
        return target

    def rename_pattern(self, row: int, name: str) -> bool:
        category = self.current_category_data
        if category is None or name == category.rules[row].name:
            return False
        category.rules[row].name = name
        self._patterns_model._cell_changed(row, PatternTableModel.NAME_COLUMN)
        self._after_edit()
        return True

    def set_pattern_regex(self, row: int, regex: str) -> bool:
        category = self.current_category_data
        if category is None or not 0 <= row < len(category.rules):
            return False
        if regex == category.rules[row].regex:
            return False
        category.rules[row].regex = regex
        self._patterns_model._cell_changed(row, PatternTableModel.REGEX_COLUMN)
        self._after_edit()
        return True

    @Slot()
    def revert(self) -> None:
        """Discard all unsaved changes."""
        name = self.current_category_data.name if self.current_category_data else ""
        self._config = self._saved.clone()
        self._reset_views(name)

    def save(self, overwrite_external_changes: bool = False) -> SaveOutcome:
        if self._issues or self._load_error:
            return SaveOutcome.INVALID
        if not overwrite_external_changes and self._changed_on_disk():
            return SaveOutcome.CONFLICT

        try:
            save_patterns_json(self._path, self._config.to_json())
        except (OSError, TypeError, ValueError) as exc:
            logger.error("Could not save patterns config '%s': %s", self._path, exc)
            self.error_occurred.emit(f"Could not save {self._path.name}:\n{exc}")
            return SaveOutcome.FAILED

        self._saved = self._config.clone()
        self._mtime_ns = self._stat_mtime()
        self._is_new_file = False
        logger.info("Saved %d pattern categories to %s", len(self._config.categories), self._path)
        self._after_edit()
        self.saved.emit(str(self._path))
        return SaveOutcome.SAVED

    # ================================================================ helpers

    def _load(self) -> None:
        if not self._path.exists():
            self._is_new_file = True
            return
        try:
            self._config = PatternConfig.from_json(load_patterns_json(self._path))
        except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
            self._load_error = f"Could not open {self._path}:\n{exc}"
            logger.error("Could not open patterns config '%s': %s", self._path, exc)
            self._config = PatternConfig()
        self._saved = self._config.clone()
        self._mtime_ns = self._stat_mtime()

    def _reset_views(self, select_name: str) -> None:
        self._current = -1
        self._patterns_model._reset()
        self._categories_model._reset()
        names = [c.name for c in self._config.categories]
        self._select(names.index(select_name) if select_name in names else 0, force=True)
        self._after_edit()

    def _stat_mtime(self) -> int | None:
        try:
            return self._path.stat().st_mtime_ns
        except OSError:
            return None

    def _changed_on_disk(self) -> bool:
        return self._stat_mtime() != self._mtime_ns

    def _after_edit(self) -> None:
        self._revalidate()
        self._update_columns()

    def _revalidate(self) -> None:
        self._issues = self._config.validate()
        self._refresh_issue_views()

        dirty = self._config != self._saved or self._is_new_file and bool(self._config.categories)
        if dirty != self._dirty:
            self._dirty = dirty
            self.dirty_changed.emit(dirty)
        can_save = dirty and not self._issues and not self._load_error
        if can_save != self._can_save:
            self._can_save = can_save
            self.can_save_changed.emit(can_save)
        self.issues_changed.emit()

    def _refresh_issue_views(self) -> None:
        categories: dict[int, str] = {}
        patterns: dict[tuple[int, IssueField], str] = {}
        for issue in self._issues:
            categories.setdefault(issue.category, issue.message)
            if issue.category == self._current and issue.rule is not None:
                patterns.setdefault((issue.rule, issue.field), issue.message)
        self._categories_model._set_issues(categories)
        self._patterns_model._set_issues(patterns)

    def _update_columns(self) -> None:
        """Columns the current category would extract, from every regex that compiles."""
        columns: list[str] = []
        category = self.current_category_data
        if category is not None:
            compiled: dict[str, dict[str, re.Pattern]] = {"base": {}, "patterns": {}}
            try:
                compiled["base"][SEPARATOR_KEY] = re.compile(category.separator)
            except re.error:
                pass
            for rule in category.rules:
                try:
                    compiled["patterns"][rule.name] = re.compile(rule.regex, PATTERN_FLAGS)
                except re.error:
                    pass
            columns = get_headers_from_patterns(compiled)
        if columns != self._columns:
            self._columns = columns
            self.columns_changed.emit(list(columns))

    def _first_issue(self, category: int, rule: int | None, field: IssueField) -> str:
        for issue in self._issues:
            if issue.category == category and issue.rule == rule and issue.field is field:
                return issue.message
        return ""

    def _issue_location(self, issue: ValidationIssue) -> str:
        category = self._config.categories[issue.category]
        name = category.name or f"Category #{issue.category + 1}"
        if issue.rule is None:
            return name
        rule = category.rules[issue.rule]
        return f"{name} › {rule.name or f'pattern #{issue.rule + 1}'}"
