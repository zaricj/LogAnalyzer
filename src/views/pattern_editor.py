"""Pattern config editor dialog: pure layout + bindings to ``PatternEditorViewModel``."""

from __future__ import annotations

from PySide6.QtCore import QModelIndex, QPersistentModelIndex, QSettings, QSignalBlocker, QSize, Qt
from PySide6.QtGui import QCloseEvent, QColor, QKeySequence, QPalette, QShortcut
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListView,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSplitter,
    QStyleOptionViewItem,
    QStyledItemDelegate,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.viewmodels.pattern_editor_viewmodel import (
    IssueRole,
    PatternEditorViewModel,
    PatternTableModel,
    SaveOutcome,
)
from src.views.theme import LIGHT, ThemeManager, Tokens, icon, mono_font
from src.views.widgets import CodeEdit, FlowLayout

ModelIndex = QModelIndex | QPersistentModelIndex

_GEOMETRY_KEY = "pattern_editor/geometry"
_SPLITTER_KEY = "pattern_editor/splitter"


def _label(text: str, name: str) -> QLabel:
    label = QLabel(text)
    label.setObjectName(name)
    return label


def _repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


def _set_invalid(widget: QWidget, invalid: bool) -> None:
    if widget.property("invalid") != invalid:
        widget.setProperty("invalid", invalid)
        _repolish(widget)


class IssueDelegate(QStyledItemDelegate):
    """Paints items that carry a validation issue in the danger colour with an alert icon."""

    def __init__(self, mono_columns: tuple[int, ...] = (), parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._mono_columns = mono_columns
        self._tokens = LIGHT
        self._alert = icon("alert", LIGHT.danger, 14)

    def set_tokens(self, tokens: Tokens) -> None:
        self._tokens = tokens
        self._alert = icon("alert", tokens.danger, 14)

    def initStyleOption(self, option: QStyleOptionViewItem, index: ModelIndex) -> None:  # noqa: N802
        super().initStyleOption(option, index)
        if index.column() in self._mono_columns:
            option.font = mono_font()
        if index.data(IssueRole):
            danger = QColor(self._tokens.danger)
            for group in (QPalette.ColorGroup.Active, QPalette.ColorGroup.Inactive):
                option.palette.setColor(group, QPalette.ColorRole.Text, danger)
                option.palette.setColor(group, QPalette.ColorRole.HighlightedText, danger)
            option.icon = self._alert
            option.decorationSize = QSize(14, 14)
            option.features |= QStyleOptionViewItem.ViewItemFeature.HasDecoration

    def createEditor(self, parent: QWidget, option: QStyleOptionViewItem, index: ModelIndex) -> QWidget:  # noqa: N802
        editor = super().createEditor(parent, option, index)
        if index.column() in self._mono_columns:
            editor.setFont(mono_font())
        return editor


class PatternEditorDialog(QDialog):
    """Edit categories, separators and regexes of a patterns config, then save."""

    def __init__(
        self,
        viewmodel: PatternEditorViewModel,
        theme: ThemeManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = viewmodel
        self._tokens: Tokens = theme.tokens if theme else LIGHT
        self._icon_targets: list[tuple[QPushButton | QToolButton, str, str]] = []
        self._loading_regex = False

        self.setObjectName("PatternEditor")
        self.setWindowTitle("Edit patterns")
        self.setMinimumSize(900, 560)
        self.resize(1180, 760)
        self.setSizeGripEnabled(True)

        self._build_ui()
        self._bind_viewmodel()
        self._apply_initial_state()
        self._apply_tokens(self._tokens)
        if theme is not None:
            theme.changed.connect(self._apply_tokens)
        self._restore_geometry()

    # ================================================================== layout

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QVBoxLayout()
        header.setContentsMargins(24, 20, 24, 14)
        header.setSpacing(2)
        header.addWidget(_label("Pattern configuration", "DialogTitle"))
        self.path_label = _label(str(self._vm.path), "DialogPath")
        self.path_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        header.addWidget(self.path_label)
        root.addLayout(header)

        self.splitter = QSplitter(Qt.Orientation.Horizontal)
        self.splitter.setChildrenCollapsible(False)
        self.splitter.setHandleWidth(14)
        self.splitter.addWidget(self._build_categories_pane())
        self.splitter.addWidget(self._build_category_pane())
        self.splitter.setStretchFactor(1, 1)
        self.splitter.setSizes([260, 900])
        body = QHBoxLayout()
        body.setContentsMargins(24, 0, 24, 18)
        body.addWidget(self.splitter)
        root.addLayout(body, 1)

        root.addWidget(self._build_footer())

        QShortcut(QKeySequence(QKeySequence.StandardKey.Save), self, activated=self._save)

    def _build_categories_pane(self) -> QWidget:
        pane = QFrame()
        pane.setObjectName("EditorPane")
        layout = QVBoxLayout(pane)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(10)

        top = QHBoxLayout()
        top.addWidget(_label("CATEGORIES", "SectionTitle"), 1)
        self.add_category_button = self._icon_button("plus", "Add category")
        self.remove_category_button = self._icon_button("trash", "Remove category")
        top.addWidget(self.add_category_button)
        top.addWidget(self.remove_category_button)
        layout.addLayout(top)

        self.category_list = QListView()
        self.category_list.setObjectName("CategoryList")
        self.category_list.setModel(self._vm.categories_model)
        self.category_list.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.category_list.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.category_list.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.category_list.setUniformItemSizes(True)
        self.category_list.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.category_delegate = IssueDelegate(parent=self.category_list)
        self.category_list.setItemDelegate(self.category_delegate)
        layout.addWidget(self.category_list, 1)
        layout.addWidget(_label("Double-click or F2 to rename.", "Hint"))
        return pane

    def _build_category_pane(self) -> QWidget:
        self.category_pane = QFrame()
        self.category_pane.setObjectName("EditorPane")
        layout = QVBoxLayout(self.category_pane)
        layout.setContentsMargins(18, 14, 18, 16)
        layout.setSpacing(8)

        # -- separator
        layout.addWidget(_label("Event separator", "FieldLabel"))
        self.separator_edit = QLineEdit()
        self.separator_edit.setFont(mono_font())
        self.separator_edit.setPlaceholderText(r"^(?P<time>\d{2}:\d{2}:\d{2})")
        layout.addWidget(self.separator_edit)
        self.separator_error = _label("", "FieldError")
        self.separator_error.setWordWrap(True)
        layout.addWidget(self.separator_error)
        layout.addWidget(
            _label(
                "Matches the first line of each event block. A (?P<time>…) group supplies the timestamp.",
                "Hint",
            )
        )
        layout.addSpacing(8)

        # -- patterns table
        bar = QHBoxLayout()
        bar.setSpacing(6)
        bar.addWidget(_label("Patterns", "FieldLabel"), 1)
        self.add_pattern_button = self._icon_button("plus", "Add pattern below the selection")
        self.remove_pattern_button = self._icon_button("trash", "Remove pattern")
        self.move_up_button = self._icon_button("arrow-up", "Move up (earlier patterns win)")
        self.move_down_button = self._icon_button("arrow-down", "Move down")
        for button in (
            self.add_pattern_button,
            self.remove_pattern_button,
            self.move_up_button,
            self.move_down_button,
        ):
            bar.addWidget(button)
        layout.addLayout(bar)

        self.pattern_table = QTableView()
        self.pattern_table.setObjectName("PatternTable")
        self.pattern_table.setModel(self._vm.patterns_model)
        self.pattern_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.pattern_table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.pattern_table.setAlternatingRowColors(True)
        self.pattern_table.setShowGrid(False)
        self.pattern_table.setWordWrap(False)
        self.pattern_table.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.pattern_table.setEditTriggers(
            QAbstractItemView.EditTrigger.DoubleClicked | QAbstractItemView.EditTrigger.EditKeyPressed
        )
        self.pattern_table.verticalHeader().setDefaultSectionSize(30)
        self.pattern_table.verticalHeader().setMinimumWidth(36)
        header = self.pattern_table.horizontalHeader()
        header.setHighlightSections(False)
        header.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header.setSectionResizeMode(PatternTableModel.NAME_COLUMN, QHeaderView.ResizeMode.Interactive)
        header.setSectionResizeMode(PatternTableModel.REGEX_COLUMN, QHeaderView.ResizeMode.Stretch)
        header.resizeSection(PatternTableModel.NAME_COLUMN, 220)
        self.pattern_delegate = IssueDelegate(
            mono_columns=(PatternTableModel.REGEX_COLUMN,), parent=self.pattern_table
        )
        self.pattern_table.setItemDelegate(self.pattern_delegate)
        self.pattern_table.setMinimumHeight(170)
        layout.addWidget(self.pattern_table, 3)
        self.category_error = _label("", "FieldError")
        layout.addWidget(self.category_error)
        layout.addSpacing(10)

        # -- regex detail editor
        self.regex_title = _label("Regex", "FieldLabel")
        layout.addWidget(self.regex_title)
        self.regex_edit = CodeEdit()
        self.regex_edit.setObjectName("RegexEdit")
        self.regex_edit.setPlaceholderText("Select a pattern to edit its regex")
        self.regex_edit.setMinimumHeight(90)
        layout.addWidget(self.regex_edit, 2)
        self.regex_error = _label("", "FieldError")
        self.regex_error.setWordWrap(True)
        layout.addWidget(self.regex_error)
        layout.addWidget(
            _label("Compiled with MULTILINE | DOTALL. Named groups (?P<name>…) become columns.", "Hint")
        )
        layout.addSpacing(6)

        # -- extracted columns
        layout.addWidget(_label("Extracted columns", "FieldLabel"))
        chips_host = QWidget()
        self.columns_flow = FlowLayout(chips_host)
        # Categories with many groups would otherwise squeeze the table; scroll instead.
        chips_scroll = QScrollArea()
        chips_scroll.setWidget(chips_host)
        chips_scroll.setWidgetResizable(True)
        chips_scroll.setFrameShape(QFrame.Shape.NoFrame)
        chips_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        chips_scroll.setMaximumHeight(76)
        chips_scroll.setStyleSheet("QScrollArea, QScrollArea > QWidget > QWidget { background: transparent; }")
        layout.addWidget(chips_scroll)
        return self.category_pane

    def _build_footer(self) -> QWidget:
        footer = QFrame()
        footer.setObjectName("DialogFooter")
        layout = QHBoxLayout(footer)
        layout.setContentsMargins(24, 14, 24, 14)
        layout.setSpacing(8)
        self.summary_label = _label("", "Summary")
        self.summary_label.setWordWrap(True)
        layout.addWidget(self.summary_label, 1)

        self.revert_button = QPushButton(" Revert")
        self.revert_button.setObjectName("Ghost")
        self.revert_button.setToolTip("Discard all unsaved changes")
        self._track_icon(self.revert_button, "undo", "text_muted")
        self.close_button = QPushButton("Close")
        self.save_button = QPushButton("  Save")
        self.save_button.setObjectName("Primary")
        self.save_button.setMinimumWidth(120)
        self.save_button.setToolTip("Save to disk (Ctrl+S)")
        self._track_icon(self.save_button, "save", "accent_text")
        for button in (self.revert_button, self.close_button, self.save_button):
            # Enter inside an editor must never trigger Save/Revert by accident.
            button.setAutoDefault(False)
            button.setDefault(False)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            layout.addWidget(button)
        return footer

    def _icon_button(self, icon_name: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._track_icon(button, icon_name, "text_muted")
        return button

    def _track_icon(self, button: QPushButton | QToolButton, name: str, token: str) -> None:
        self._icon_targets.append((button, name, token))

    # ================================================================== theme

    def _apply_tokens(self, tokens: Tokens) -> None:
        self._tokens = tokens
        for button, name, token in self._icon_targets:
            button.setIcon(icon(name, getattr(tokens, token), 16))
        for delegate in (self.category_delegate, self.pattern_delegate):
            delegate.set_tokens(tokens)
        self.category_list.viewport().update()
        self.pattern_table.viewport().update()

    # ================================================================ binding

    def _bind_viewmodel(self) -> None:
        vm = self._vm

        # View -> ViewModel
        self.category_list.selectionModel().currentRowChanged.connect(
            lambda current, _prev: vm.select_category(current.row())
        )
        self.add_category_button.clicked.connect(self._add_category)
        self.remove_category_button.clicked.connect(self._remove_category)
        self.separator_edit.textEdited.connect(vm.set_separator)
        self.pattern_table.selectionModel().currentRowChanged.connect(
            lambda current, _prev: self._load_regex_editor(current.row())
        )
        self.add_pattern_button.clicked.connect(self._add_pattern)
        self.remove_pattern_button.clicked.connect(self._remove_pattern)
        self.move_up_button.clicked.connect(lambda: self._move_pattern(-1))
        self.move_down_button.clicked.connect(lambda: self._move_pattern(+1))
        self.regex_edit.textChanged.connect(self._on_regex_edited)
        self.save_button.clicked.connect(self._save)
        self.revert_button.clicked.connect(self._revert)
        self.close_button.clicked.connect(self.reject)

        # ViewModel -> View
        vm.current_category_changed.connect(self._on_category_changed)
        vm.separator_changed.connect(self._set_separator_text)
        vm.columns_changed.connect(self._set_columns)
        vm.issues_changed.connect(self._update_issues)
        vm.dirty_changed.connect(self._on_dirty_changed)
        vm.can_save_changed.connect(self.save_button.setEnabled)
        vm.error_occurred.connect(lambda message: QMessageBox.critical(self, "Save failed", message))

        patterns = vm.patterns_model
        patterns.dataChanged.connect(self._on_patterns_data_changed)
        for signal in (patterns.rowsInserted, patterns.rowsRemoved, patterns.rowsMoved, patterns.modelReset):
            signal.connect(self._update_pattern_buttons)

    def _apply_initial_state(self) -> None:
        self._on_category_changed(self._vm.current_category)
        self._set_columns(self._vm.columns)
        self._on_dirty_changed(self._vm.is_dirty)
        self.save_button.setEnabled(self._vm.can_save)
        self._update_issues()

    # ============================================================ VM -> View

    def _on_category_changed(self, row: int) -> None:
        index = self._vm.categories_model.index(row) if row >= 0 else QModelIndex()
        if self.category_list.currentIndex() != index:
            with QSignalBlocker(self.category_list.selectionModel()):
                self.category_list.setCurrentIndex(index)
        has_category = row >= 0
        self.category_pane.setEnabled(has_category)
        self.remove_category_button.setEnabled(has_category)
        self._set_separator_text(self._vm.separator)
        first = self._vm.patterns_model.index(0, 0)
        self.pattern_table.setCurrentIndex(first)  # invalid index if the table is empty
        self._load_regex_editor(first.row())

    def _set_separator_text(self, text: str) -> None:
        if self.separator_edit.text() != text:
            with QSignalBlocker(self.separator_edit):
                self.separator_edit.setText(text)
                self.separator_edit.setCursorPosition(0)

    def _set_columns(self, columns: list[str]) -> None:
        self.columns_flow.clear()
        if not columns:
            self.columns_flow.addWidget(_label("No named groups yet", "ChipEmpty"))
        for column in columns:
            self.columns_flow.addWidget(_label(column, "Chip"))
        self.columns_flow.parentWidget().updateGeometry()

    def _update_issues(self) -> None:
        vm = self._vm
        separator_issue = vm.separator_issue()
        self.separator_error.setText(separator_issue)
        self.separator_error.setVisible(bool(separator_issue))
        _set_invalid(self.separator_edit, bool(separator_issue))

        category_issue = vm.category_issue()
        self.category_error.setText(category_issue)
        self.category_error.setVisible(bool(category_issue))

        row = self._current_pattern_row()
        pattern_issue = vm.pattern_issue(row) if row >= 0 else ""
        self.regex_error.setText(pattern_issue)
        self.regex_error.setVisible(bool(pattern_issue))
        _set_invalid(self.regex_edit, bool(pattern_issue))

        self.summary_label.setText(vm.summary())
        tone = "danger" if vm.issue_count else ("warning" if vm.is_dirty else "")
        if self.summary_label.property("tone") != tone:
            self.summary_label.setProperty("tone", tone)
            _repolish(self.summary_label)

    def _on_dirty_changed(self, dirty: bool) -> None:
        self.revert_button.setEnabled(dirty)
        self.setWindowTitle(f"Edit patterns{' •' if dirty else ''} — {self._vm.path.name}")

    def _on_patterns_data_changed(self, top_left: QModelIndex, bottom_right: QModelIndex, roles: list[int]) -> None:
        if roles and Qt.ItemDataRole.EditRole not in roles and Qt.ItemDataRole.DisplayRole not in roles:
            return  # issue-only refresh
        row = self._current_pattern_row()
        if top_left.row() <= row <= bottom_right.row():
            text = self._vm.pattern_regex(row)
            if self.regex_edit.toPlainText() != text:
                self._load_regex_editor(row)
            self.regex_title.setText(self._regex_title(row))

    def _update_pattern_buttons(self, *_: object) -> None:
        row = self._current_pattern_row()
        count = self._vm.patterns_model.rowCount()
        self.remove_pattern_button.setEnabled(row >= 0)
        self.move_up_button.setEnabled(row > 0)
        self.move_down_button.setEnabled(0 <= row < count - 1)

    # ============================================================ View -> VM

    def _current_pattern_row(self) -> int:
        index = self.pattern_table.currentIndex()
        return index.row() if index.isValid() else -1

    def _regex_title(self, row: int) -> str:
        if row < 0:
            return "Regex"
        name = self._vm.patterns_model.index(row, PatternTableModel.NAME_COLUMN).data()
        return f"Regex — {name}" if name else "Regex"

    def _load_regex_editor(self, row: int) -> None:
        self._loading_regex = True
        try:
            self.regex_edit.setPlainText(self._vm.pattern_regex(row) if row >= 0 else "")
        finally:
            self._loading_regex = False
        self.regex_edit.setEnabled(row >= 0)
        self.regex_title.setText(self._regex_title(row))
        self._update_pattern_buttons()
        self._update_issues()

    def _on_regex_edited(self) -> None:
        row = self._current_pattern_row()
        if self._loading_regex or row < 0:
            return
        self._vm.set_pattern_regex(row, self.regex_edit.toPlainText())

    def _add_category(self) -> None:
        row = self._vm.add_category()
        index = self._vm.categories_model.index(row)
        self.category_list.scrollTo(index)
        self.category_list.edit(index)

    def _remove_category(self) -> None:
        category = self._vm.current_category_data
        if category is None:
            return
        if category.rules:
            answer = QMessageBox.question(
                self,
                "Remove category",
                f"Remove category '{category.name}' and its {len(category.rules)} pattern(s)?\n\n"
                "Nothing is written to disk until you save.",
            )
            if answer != QMessageBox.StandardButton.Yes:
                return
        self._vm.remove_category(self._vm.current_category)

    def _add_pattern(self) -> None:
        row = self._vm.add_pattern(self._current_pattern_row())
        if row < 0:
            return
        index = self._vm.patterns_model.index(row, PatternTableModel.NAME_COLUMN)
        self.pattern_table.setCurrentIndex(index)
        self.pattern_table.scrollTo(index)
        self.pattern_table.edit(index)

    def _remove_pattern(self) -> None:
        row = self._current_pattern_row()
        if row < 0:
            return
        self._vm.remove_pattern(row)
        count = self._vm.patterns_model.rowCount()
        next_index = self._vm.patterns_model.index(min(row, count - 1), 0)
        self.pattern_table.setCurrentIndex(next_index)
        self._load_regex_editor(next_index.row())

    def _move_pattern(self, delta: int) -> None:
        row = self._current_pattern_row()
        if row < 0:
            return
        new_row = self._vm.move_pattern(row, delta)
        self.pattern_table.setCurrentIndex(self._vm.patterns_model.index(new_row, 0))
        self._update_pattern_buttons()

    def _save(self) -> bool:
        self._commit_open_editors()
        outcome = self._vm.save()
        if outcome is SaveOutcome.CONFLICT:
            answer = QMessageBox.warning(
                self,
                "File changed on disk",
                f"{self._vm.path.name} was modified outside the editor since it was opened.\n\n"
                "Overwrite it with your version?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Cancel,
            )
            if answer == QMessageBox.StandardButton.Yes:
                outcome = self._vm.save(overwrite_external_changes=True)
        elif outcome is SaveOutcome.INVALID:
            QMessageBox.warning(
                self,
                "Cannot save",
                f"Fix the {self._vm.issue_count} problem(s) first:\n\n{self._vm.summary()}",
            )
        return outcome is SaveOutcome.SAVED

    def _revert(self) -> None:
        answer = QMessageBox.question(self, "Revert changes", "Discard all unsaved changes?")
        if answer == QMessageBox.StandardButton.Yes:
            self._vm.revert()

    def _commit_open_editors(self) -> None:
        """Finish an in-progress inline edit so Save sees the latest text."""
        for view in (self.category_list, self.pattern_table):
            if view.state() == QAbstractItemView.State.EditingState:
                view.setFocus()  # focus change commits the delegate's editor

    # ============================================================== closing

    def reject(self) -> None:
        """Close (Esc / Close button / window ✕): ask before dropping unsaved changes."""
        self._commit_open_editors()
        if self._vm.is_dirty:
            answer = QMessageBox.question(
                self,
                "Unsaved changes",
                "Save your changes to the patterns config before closing?",
                QMessageBox.StandardButton.Save
                | QMessageBox.StandardButton.Discard
                | QMessageBox.StandardButton.Cancel,
                QMessageBox.StandardButton.Save,
            )
            if answer == QMessageBox.StandardButton.Cancel:
                return
            if answer == QMessageBox.StandardButton.Save and not self._save():
                return
        self._store_geometry()
        super().reject()

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt override
        # QDialog routes the window ✕ through reject(); ignore here so a
        # cancelled "unsaved changes" prompt keeps the dialog open.
        event.ignore()
        self.reject()

    def _restore_geometry(self) -> None:
        settings = QSettings("Glint", "Glint")
        if geometry := settings.value(_GEOMETRY_KEY):
            self.restoreGeometry(geometry)
        if state := settings.value(_SPLITTER_KEY):
            self.splitter.restoreState(state)

    def _store_geometry(self) -> None:
        settings = QSettings("Glint", "Glint")
        settings.setValue(_GEOMETRY_KEY, self.saveGeometry())
        settings.setValue(_SPLITTER_KEY, self.splitter.saveState())
