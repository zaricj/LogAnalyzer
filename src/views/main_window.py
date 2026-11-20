"""Main window: pure layout + bindings to ``MainViewModel``. No processing logic here."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QSignalBlocker, Qt, QTimer, QUrl
from PySide6.QtGui import (
    QCloseEvent,
    QColor,
    QDesktopServices,
    QIcon,
    QKeySequence,
    QShortcut,
    QTextCharFormat,
)
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QStackedWidget,
    QTableView,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.models import SearchResult, SearchStatus
from src.viewmodels.main_viewmodel import PROGRESS_MAX, MainViewModel
from src.views.theme import APP_LOGO_PATH, LIGHT, ThemeManager, ThemeMode, Tokens, icon, mono_font
from src.views.widgets import FlowLayout, ToggleSwitch

SIDEBAR_WIDTH = 372


def _set_text_silently(edit: QLineEdit, text: str) -> None:
    """Update a line edit from the ViewModel without re-triggering its signals."""
    if edit.text() != text:
        with QSignalBlocker(edit):
            edit.setText(text)
            edit.setCursorPosition(0)  # show the start of long paths
    edit.setToolTip(text if len(text) > 40 else "")


def _label(text: str, name: str, parent: QWidget | None = None) -> QLabel:
    label = QLabel(text, parent)
    label.setObjectName(name)
    return label


def _repolish(widget: QWidget) -> None:
    widget.style().unpolish(widget)
    widget.style().polish(widget)


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: MainViewModel, theme: ThemeManager | None = None) -> None:
        super().__init__()
        self._vm = viewmodel
        self._theme = theme
        self._tokens: Tokens = theme.tokens if theme else LIGHT
        self._icon_targets: list[tuple[QPushButton | QToolButton, str, str]] = []
        self._log_colors: dict[int, QColor] = {}

        self._elapsed = QElapsedTimer()
        self._tick = QTimer(self)
        self._tick.setInterval(200)
        self._tick.timeout.connect(self._update_elapsed)

        self.setWindowTitle("Glint")
        self.resize(1320, 820)
        self.setMinimumSize(1000, 640)

        self._build_ui()
        self._bind_viewmodel()
        self._apply_initial_state()
        self._apply_tokens(self._tokens)
        if theme is not None:
            theme.changed.connect(self._apply_tokens)
            theme.mode_changed.connect(lambda _: self._update_theme_button())

    # ================================================================== layout

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)
        root.addWidget(self._build_sidebar())
        root.addWidget(self._build_content(), 1)
        self.setCentralWidget(central)

        QShortcut(QKeySequence("Ctrl+Return"), self, activated=self._vm.start_search)
        QShortcut(QKeySequence("Ctrl+Enter"), self, activated=self._vm.start_search)
        QShortcut(QKeySequence("Escape"), self, activated=self._vm.cancel_search)

    # ---------------------------------------------------------------- sidebar

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        outer = QVBoxLayout(sidebar)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Brand
        brand = QWidget()
        brand_layout = QHBoxLayout(brand)
        brand_layout.setContentsMargins(24, 22, 24, 18)
        brand_layout.setSpacing(12)
        self.brand_mark = _label("", "BrandMark")
        self.brand_mark.setFixedSize(36, 36)
        self.brand_mark.setPixmap(QIcon(str(APP_LOGO_PATH)).pixmap(36, 36))
        self.brand_mark.setAlignment(Qt.AlignmentFlag.AlignCenter)
        titles = QVBoxLayout()
        titles.setSpacing(0)
        titles.addWidget(_label("Glint", "BrandTitle"))
        titles.addWidget(_label("Log pattern extraction", "BrandSubtitle"))
        self.theme_button = QToolButton()
        self.theme_button.setObjectName("ThemeButton")
        self.theme_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_button.setVisible(self._theme is not None)
        if self._theme is not None:
            self.theme_button.clicked.connect(self._theme.cycle_mode)
        brand_layout.addWidget(self.brand_mark)
        brand_layout.addLayout(titles, 1)
        brand_layout.addWidget(self.theme_button, 0, Qt.AlignmentFlag.AlignVCenter)
        outer.addWidget(brand)

        # Scrollable form
        form = QWidget()
        form_layout = QVBoxLayout(form)
        form_layout.setContentsMargins(24, 4, 24, 20)
        form_layout.setSpacing(14)

        # -- Pattern
        form_layout.addWidget(_label("PATTERN", "SectionTitle"))
        self.patterns_edit = QLineEdit()
        self.patterns_edit.setPlaceholderText("patterns.json")
        self.browse_patterns_button = self._icon_button("file", "Choose patterns config…")
        self.browse_patterns_button.clicked.connect(self._browse_patterns_config)
        form_layout.addLayout(self._field("Config file", self.patterns_edit, self.browse_patterns_button))

        self.pattern_combo = QComboBox()
        self.pattern_combo.setSizeAdjustPolicy(QComboBox.SizeAdjustPolicy.AdjustToMinimumContentsLengthWithIcon)
        self.pattern_combo.setMinimumContentsLength(12)
        self.reload_button = self._icon_button("refresh", "Reload patterns config")
        form_layout.addLayout(self._field("Pattern key", self.pattern_combo, self.reload_button))

        columns_box = QVBoxLayout()
        columns_box.setSpacing(6)
        columns_box.addWidget(_label("Extracted columns", "FieldLabel"))
        chips_host = QWidget()
        self.columns_flow = FlowLayout(chips_host)
        columns_box.addWidget(chips_host)
        form_layout.addLayout(columns_box)

        form_layout.addSpacing(6)
        form_layout.addWidget(self._divider())
        form_layout.addSpacing(2)

        # -- Source
        form_layout.addWidget(_label("SOURCE", "SectionTitle"))
        self.files_dir_edit = QLineEdit()
        self.files_dir_edit.setPlaceholderText("Folder containing the log files")
        self.browse_files_button = self._icon_button("folder", "Choose log directory…")
        self.browse_files_button.clicked.connect(self._browse_files_directory)
        form_layout.addLayout(self._field("Log directory", self.files_dir_edit, self.browse_files_button))

        self.file_pattern_edit = QLineEdit()
        self.file_pattern_edit.setPlaceholderText("*.log")
        form_layout.addLayout(self._field("File pattern", self.file_pattern_edit, hint="Glob, e.g. *.log or server_*.txt"))

        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Optional")
        self.keyword_edit.setClearButtonEnabled(True)
        form_layout.addLayout(
            self._field("Event keyword", self.keyword_edit, hint="Only events containing this text (case-insensitive)")
        )

        form_layout.addSpacing(6)
        form_layout.addWidget(self._divider())
        form_layout.addSpacing(2)

        # -- Output
        form_layout.addWidget(_label("OUTPUT", "SectionTitle"))
        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Folder for CSV / Excel reports")
        self.browse_output_button = self._icon_button("folder", "Choose output directory…")
        self.browse_output_button.clicked.connect(self._browse_output_directory)
        form_layout.addLayout(self._field("Output directory", self.output_dir_edit, self.browse_output_button))

        excel_row = QHBoxLayout()
        excel_text = QVBoxLayout()
        excel_text.setSpacing(1)
        excel_text.addWidget(_label("Export to Excel", "FieldLabel"))
        excel_text.addWidget(_label("Adds an .xlsx next to the CSV (≤ 1,048,575 rows)", "Hint"))
        self.excel_switch = ToggleSwitch()
        excel_row.addLayout(excel_text, 1)
        excel_row.addWidget(self.excel_switch, 0, Qt.AlignmentFlag.AlignVCenter)
        form_layout.addLayout(excel_row)
        form_layout.addStretch(1)

        scroll = QScrollArea()
        scroll.setWidget(form)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        outer.addWidget(scroll, 1)

        # Footer with run / cancel
        footer = QFrame()
        footer.setObjectName("SidebarFooter")
        footer_layout = QVBoxLayout(footer)
        footer_layout.setContentsMargins(24, 16, 24, 20)
        footer_layout.setSpacing(10)
        self.validation_label = _label("", "Validation")
        self.validation_label.setWordWrap(True)
        self.start_button = QPushButton("  Run search")
        self.start_button.setObjectName("Primary")
        self.start_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.start_button.setToolTip("Run search (Ctrl+Enter)")
        self.cancel_button = QPushButton("  Cancel")
        self.cancel_button.setObjectName("Danger")
        self.cancel_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.cancel_button.setToolTip("Cancel search (Esc)")
        self._track_icon(self.start_button, "play", "accent_text")
        self._track_icon(self.cancel_button, "stop", "danger")
        footer_layout.addWidget(self.validation_label)
        footer_layout.addWidget(self.start_button)
        footer_layout.addWidget(self.cancel_button)
        outer.addWidget(footer)
        return sidebar

    # ---------------------------------------------------------------- content

    def _build_content(self) -> QWidget:
        content = QWidget()
        content.setObjectName("Content")
        layout = QVBoxLayout(content)
        layout.setContentsMargins(32, 24, 32, 24)
        layout.setSpacing(18)

        # Header: title + status, actions on the right
        header = QHBoxLayout()
        header.setSpacing(12)
        heading = QVBoxLayout()
        heading.setSpacing(6)
        title_row = QHBoxLayout()
        title_row.setSpacing(12)
        title_row.addWidget(_label("Results", "PageTitle"))
        self.status_pill = _label("Idle", "Pill")
        title_row.addWidget(self.status_pill, 0, Qt.AlignmentFlag.AlignVCenter)
        title_row.addStretch(1)
        heading.addLayout(title_row)
        self.status_label = _label("", "StatusText")
        self.status_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        heading.addWidget(self.status_label)
        header.addLayout(heading, 1)

        self.open_csv_button = self._ghost_button("Open CSV", "file")
        self.open_excel_button = self._ghost_button("Open Excel", "sheet")
        self.open_folder_button = self._ghost_button("Output folder", "folder")
        for button in (self.open_csv_button, self.open_excel_button, self.open_folder_button):
            header.addWidget(button, 0, Qt.AlignmentFlag.AlignTop)
        layout.addLayout(header)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, PROGRESS_MAX)
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Stat tiles
        stats = QHBoxLayout()
        stats.setSpacing(14)
        self.rows_stat = self._stat_card("Rows matched", "—")
        self.files_stat = self._stat_card("Files searched", "—")
        self.time_stat = self._stat_card("Elapsed", "—")
        self.output_stat = self._stat_card("Output file", "—", small=True)
        for card in (self.rows_stat, self.files_stat, self.time_stat):
            stats.addWidget(card[0], 2)
        stats.addWidget(self.output_stat[0], 3)
        layout.addLayout(stats)

        # Results / log card
        card = QFrame()
        card.setObjectName("Card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(0, 0, 0, 0)
        card_layout.setSpacing(0)

        toolbar = QHBoxLayout()
        toolbar.setContentsMargins(14, 12, 16, 12)
        segmented = QFrame()
        segmented.setObjectName("Segmented")
        seg_layout = QHBoxLayout(segmented)
        seg_layout.setContentsMargins(3, 3, 3, 3)
        seg_layout.setSpacing(2)
        self.preview_tab = QPushButton(" Preview")
        self.log_tab = QPushButton(" Activity log")
        self._tab_group = QButtonGroup(self)
        for index, (button, icon_name) in enumerate(((self.preview_tab, "table"), (self.log_tab, "terminal"))):
            button.setCheckable(True)
            button.setCursor(Qt.CursorShape.PointingHandCursor)
            self._tab_group.addButton(button, index)
            self._track_icon(button, icon_name, "text_muted")
            seg_layout.addWidget(button)
        self.preview_tab.setChecked(True)
        toolbar.addWidget(segmented)
        toolbar.addStretch(1)
        self.card_caption = _label("", "CardCaption")
        toolbar.addWidget(self.card_caption)
        card_layout.addLayout(toolbar)
        card_layout.addWidget(self._divider())

        # Preview: empty state or table
        self.results_view = QTableView()
        self.results_view.setModel(self._vm.results_model)
        self.results_view.setAlternatingRowColors(True)
        self.results_view.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.results_view.setWordWrap(False)
        self.results_view.setShowGrid(False)
        self.results_view.setFrameShape(QFrame.Shape.NoFrame)
        self.results_view.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.results_view.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.results_view.verticalHeader().setDefaultSectionSize(30)
        self.results_view.verticalHeader().setMinimumWidth(44)
        header_view = self.results_view.horizontalHeader()
        header_view.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header_view.setDefaultSectionSize(180)
        header_view.setStretchLastSection(True)
        header_view.setDefaultAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
        header_view.setHighlightSections(False)

        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setSpacing(8)
        empty_layout.addStretch(1)
        self.empty_icon = QLabel()
        self.empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_title = _label("No results yet", "EmptyTitle")
        self.empty_text = _label("Configure a search on the left and press Run search.", "EmptyText")
        for widget in (self.empty_icon, self.empty_title, self.empty_text):
            widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_layout.addWidget(widget)
        empty_layout.addStretch(1)

        self.preview_stack = QStackedWidget()
        self.preview_stack.addWidget(self.empty_state)
        self.preview_stack.addWidget(self.results_view)

        self.log_view = QPlainTextEdit()
        self.log_view.setObjectName("LogView")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        self.log_view.setFont(mono_font())
        self.log_view.setFrameShape(QFrame.Shape.NoFrame)

        self.pages = QStackedWidget()
        self.pages.addWidget(self.preview_stack)
        self.pages.addWidget(self.log_view)
        self._tab_group.idClicked.connect(self._show_page)
        card_layout.addWidget(self.pages, 1)

        layout.addWidget(card, 1)
        return content

    # -------------------------------------------------------------- builders

    def _field(
        self, title: str, editor: QWidget, button: QWidget | None = None, hint: str = ""
    ) -> QVBoxLayout:
        box = QVBoxLayout()
        box.setSpacing(6)
        box.addWidget(_label(title, "FieldLabel"))
        row = QHBoxLayout()
        row.setSpacing(6)
        row.addWidget(editor, 1)
        if button is not None:
            row.addWidget(button)
        box.addLayout(row)
        if hint:
            box.addWidget(_label(hint, "Hint"))
        return box

    def _icon_button(self, icon_name: str, tooltip: str) -> QToolButton:
        button = QToolButton()
        button.setToolTip(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._track_icon(button, icon_name, "text_muted")
        return button

    def _ghost_button(self, text: str, icon_name: str) -> QPushButton:
        button = QPushButton(f" {text}")
        button.setObjectName("Ghost")
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._track_icon(button, icon_name, "text_muted")
        return button

    def _stat_card(self, title: str, value: str, small: bool = False) -> tuple[QFrame, QLabel]:
        card = QFrame()
        card.setObjectName("StatCard")
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(4)
        layout.addWidget(_label(title, "StatLabel"))
        value_label = _label(value, "StatValueSmall" if small else "StatValue")
        value_label.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Preferred)
        value_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(value_label)
        if small:
            layout.addStretch(1)
        return card, value_label

    @staticmethod
    def _divider() -> QFrame:
        line = QFrame()
        line.setObjectName("Divider")
        return line

    def _track_icon(self, button: QPushButton | QToolButton, name: str, token: str) -> None:
        """Remember which tinted icon a button uses so it can follow theme changes."""
        self._icon_targets.append((button, name, token))

    # ================================================================= theme

    def _apply_tokens(self, tokens: Tokens) -> None:
        self._tokens = tokens
        for button, name, token in self._icon_targets:
            button.setIcon(icon(name, getattr(tokens, token), 16))
        self.empty_icon.setPixmap(icon("inbox", tokens.text_faint, 40).pixmap(40, 40))
        self.excel_switch.set_tokens(tokens)
        self._update_theme_button()
        self._log_colors = {
            logging.WARNING: QColor(tokens.warning),
            logging.ERROR: QColor(tokens.danger),
            logging.CRITICAL: QColor(tokens.danger),
        }

    _THEME_ICONS = {ThemeMode.SYSTEM: "monitor", ThemeMode.LIGHT: "sun", ThemeMode.DARK: "moon"}

    def _update_theme_button(self) -> None:
        if self._theme is None:
            return
        mode = self._theme.mode
        self.theme_button.setIcon(icon(self._THEME_ICONS[mode], self._tokens.text_muted, 16))
        self.theme_button.setToolTip(
            f"Theme: {mode.label} — click for {mode.next().label}"
        )

    # ================================================================= binding

    def _bind_viewmodel(self) -> None:
        vm = self._vm

        # View -> ViewModel
        self.patterns_edit.editingFinished.connect(lambda: vm.set_patterns_config(self.patterns_edit.text()))
        self.pattern_combo.currentTextChanged.connect(vm.set_pattern_key)
        self.reload_button.clicked.connect(vm.reload_patterns)
        self.files_dir_edit.textChanged.connect(vm.set_files_directory)
        self.file_pattern_edit.textChanged.connect(vm.set_file_pattern)
        self.keyword_edit.textChanged.connect(vm.set_event_keyword)
        self.output_dir_edit.textChanged.connect(vm.set_output_directory)
        self.excel_switch.toggled.connect(vm.set_export_excel)
        self.start_button.clicked.connect(vm.start_search)
        self.cancel_button.clicked.connect(vm.cancel_search)
        self.open_folder_button.clicked.connect(self._open_output_folder)
        self.open_csv_button.clicked.connect(lambda: self._open_result_file("csv_path"))
        self.open_excel_button.clicked.connect(lambda: self._open_result_file("excel_path"))

        # ViewModel -> View
        vm.patterns_config_changed.connect(lambda t: _set_text_silently(self.patterns_edit, t))
        vm.files_directory_changed.connect(lambda t: _set_text_silently(self.files_dir_edit, t))
        vm.file_pattern_changed.connect(lambda t: _set_text_silently(self.file_pattern_edit, t))
        vm.event_keyword_changed.connect(lambda t: _set_text_silently(self.keyword_edit, t))
        vm.output_directory_changed.connect(lambda t: _set_text_silently(self.output_dir_edit, t))
        vm.export_excel_changed.connect(self._set_excel_checked)
        vm.pattern_keys_changed.connect(self._set_pattern_keys)
        vm.pattern_key_changed.connect(self._select_pattern_key)
        vm.pattern_columns_changed.connect(self._set_columns)
        vm.can_start_changed.connect(self._update_start_enabled)
        vm.validation_message_changed.connect(self._set_validation)
        vm.running_changed.connect(self._on_running_changed)
        vm.progress_changed.connect(self.progress_bar.setValue)
        vm.progress_busy_changed.connect(self._set_progress_busy)
        vm.status_text_changed.connect(self.status_label.setText)
        vm.stats_changed.connect(self._set_stats)
        vm.log_message.connect(self._append_log)
        vm.search_finished.connect(self._on_search_finished)

        model = vm.results_model
        model.modelReset.connect(self._update_preview_state)
        model.rowsInserted.connect(self._update_preview_state)

    def _apply_initial_state(self) -> None:
        vm = self._vm
        _set_text_silently(self.patterns_edit, vm.patterns_config)
        _set_text_silently(self.files_dir_edit, vm.files_directory)
        _set_text_silently(self.file_pattern_edit, vm.file_pattern)
        _set_text_silently(self.keyword_edit, vm.event_keyword)
        _set_text_silently(self.output_dir_edit, vm.output_directory)
        self._set_excel_checked(vm.export_excel)
        self._set_pattern_keys(vm.pattern_keys)
        self._select_pattern_key(vm.pattern_key)
        self._set_columns(vm.pattern_columns)
        self._set_validation(vm.validation_message)
        self.status_label.setText(vm.status_text)
        self._set_pill("Idle", "idle")
        self._on_running_changed(vm.is_running)
        self._update_result_buttons(vm.last_result)
        self._update_preview_state()

    # ============================================================ VM -> View

    def _set_excel_checked(self, checked: bool) -> None:
        with QSignalBlocker(self.excel_switch):
            self.excel_switch.setChecked(checked)

    def _set_pattern_keys(self, keys: list[str]) -> None:
        with QSignalBlocker(self.pattern_combo):
            self.pattern_combo.clear()
            self.pattern_combo.addItems(keys)
        self._select_pattern_key(self._vm.pattern_key)

    def _select_pattern_key(self, key: str) -> None:
        index = self.pattern_combo.findText(key)
        if index != self.pattern_combo.currentIndex():
            with QSignalBlocker(self.pattern_combo):
                self.pattern_combo.setCurrentIndex(index)

    def _set_columns(self, columns: list[str]) -> None:
        self.columns_flow.clear()
        if not columns:
            self.columns_flow.addWidget(_label("No pattern selected", "ChipEmpty"))
        for column in columns:
            self.columns_flow.addWidget(_label(column, "Chip"))
        self.columns_flow.parentWidget().updateGeometry()

    def _set_validation(self, message: str) -> None:
        self.validation_label.setText(message)
        self.validation_label.setVisible(bool(message) and not self._vm.is_running)

    def _update_start_enabled(self, *_: object) -> None:
        self.start_button.setEnabled(self._vm.can_start)

    def _on_running_changed(self, running: bool) -> None:
        for widget in (
            self.patterns_edit,
            self.browse_patterns_button,
            self.pattern_combo,
            self.reload_button,
            self.files_dir_edit,
            self.browse_files_button,
            self.file_pattern_edit,
            self.keyword_edit,
            self.output_dir_edit,
            self.browse_output_button,
            self.excel_switch,
        ):
            widget.setEnabled(not running)
        self.start_button.setVisible(not running)
        self.cancel_button.setVisible(running)
        self._update_start_enabled()
        self._set_validation(self._vm.validation_message)
        if running:
            self._update_result_buttons(None)
            self._set_pill("Running", "running")
            self.time_stat[1].setText("0.0 s")
            self.output_stat[1].setText("—")
            self._elapsed.start()
            self._tick.start()
            self.preview_tab.setChecked(True)
            self._show_page(0)
        else:
            self._tick.stop()

    def _set_progress_busy(self, busy: bool) -> None:
        self.progress_bar.setRange(0, 0 if busy else PROGRESS_MAX)

    def _set_stats(self, rows: int, files_done: int, file_count: int) -> None:
        self.rows_stat[1].setText(f"{rows:,}")
        self.files_stat[1].setText(f"{files_done:,} / {file_count:,}" if file_count else "—")

    def _update_elapsed(self) -> None:
        self.time_stat[1].setText(f"{self._elapsed.elapsed() / 1000:.1f} s")

    def _set_pill(self, text: str, tone: str) -> None:
        self.status_pill.setText(text)
        self.status_pill.setProperty("tone", tone)
        _repolish(self.status_pill)

    def _append_log(self, level: int, message: str) -> None:
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        fmt = QTextCharFormat()
        color = self._log_colors.get(level)
        if color is not None:
            fmt.setForeground(color)
        if not self.log_view.document().isEmpty():
            cursor.insertBlock()
        cursor.insertText(message, fmt)
        bar = self.log_view.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _on_search_finished(self, result: SearchResult) -> None:
        self._update_result_buttons(result)
        self._tick.stop()
        self.time_stat[1].setText(f"{result.elapsed_seconds:.2f} s")
        match result.status:
            case SearchStatus.COMPLETED:
                self._set_pill("Completed", "success")
                self.output_stat[1].setText(result.csv_path.name if result.csv_path else "—")
                self.output_stat[1].setToolTip(str(result.csv_path or ""))
                self.results_view.resizeColumnsToContents()
                header = self.results_view.horizontalHeader()
                for col in range(header.count()):
                    header.resizeSection(col, min(max(header.sectionSize(col) + 16, 90), 420))
            case SearchStatus.NO_MATCHES:
                self._set_pill("No matches", "warning")
                self.rows_stat[1].setText("0")
                self.empty_title.setText("No matches found")
                self.empty_text.setText("Try a different pattern key, file pattern or keyword.")
            case SearchStatus.CANCELLED:
                self._set_pill("Cancelled", "warning")
            case SearchStatus.FAILED:
                self._set_pill("Failed", "danger")
                self.log_tab.setChecked(True)
                self._show_page(1)
        self._update_preview_state()

    def _update_preview_state(self, *_: object) -> None:
        rows = self._vm.results_model.rowCount()
        self.preview_stack.setCurrentIndex(1 if rows else 0)
        if rows:
            result = self._vm.last_result
            total = result.rows_written if result else 0
            if total > rows:
                self.card_caption.setText(f"Previewing first {rows:,} of {total:,} rows · full result in the CSV")
            else:
                self.card_caption.setText(f"{rows:,} rows")
        elif not self._vm.is_running and self._vm.last_result is None:
            self.empty_title.setText("No results yet")
            self.empty_text.setText("Configure a search on the left and press Run search.")
            self.card_caption.setText("")
        else:
            self.card_caption.setText("")

    def _show_page(self, index: int) -> None:
        self.pages.setCurrentIndex(index)

    def _update_result_buttons(self, result: SearchResult | None) -> None:
        has_csv = bool(result and result.csv_path and result.csv_path.exists())
        has_excel = bool(result and result.excel_path and result.excel_path.exists())
        self.open_csv_button.setEnabled(has_csv)
        self.open_excel_button.setEnabled(has_excel)

    # ======================================================== user actions

    def _browse_patterns_config(self) -> None:
        start = self._vm.patterns_config or str(Path.cwd())
        path, _ = QFileDialog.getOpenFileName(
            self, "Select patterns config", start, "JSON files (*.json);;All files (*)"
        )
        if path:
            self._vm.set_patterns_config(path)

    def _browse_files_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select log directory", self._vm.files_directory or str(Path.cwd())
        )
        if path:
            self._vm.set_files_directory(path)

    def _browse_output_directory(self) -> None:
        path = QFileDialog.getExistingDirectory(
            self, "Select output directory", self._vm.output_directory or str(Path.cwd())
        )
        if path:
            self._vm.set_output_directory(path)

    def _open_output_folder(self) -> None:
        folder = Path(self._vm.output_directory)
        folder.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder.resolve())))

    def _open_result_file(self, attr: str) -> None:
        result = self._vm.last_result
        path: Path | None = getattr(result, attr, None) if result else None
        if path is not None and path.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(path.resolve())))

    def closeEvent(self, event: QCloseEvent) -> None:  # noqa: N802 - Qt override
        self._vm.shutdown()
        super().closeEvent(event)
