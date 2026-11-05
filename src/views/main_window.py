"""Main window: pure layout + bindings to ``MainViewModel``. No processing logic here."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import QSignalBlocker, Qt, QUrl
from PySide6.QtGui import QCloseEvent, QColor, QDesktopServices, QFont, QTextCharFormat
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSplitter,
    QStatusBar,
    QStyle,
    QTableView,
    QTabWidget,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from src.models import SearchResult, SearchStatus
from src.viewmodels.main_viewmodel import PROGRESS_MAX, MainViewModel

_LOG_COLORS = {
    logging.WARNING: QColor("#c27c0e"),
    logging.ERROR: QColor("#d13438"),
    logging.CRITICAL: QColor("#d13438"),
}


def _set_text_silently(edit: QLineEdit, text: str) -> None:
    """Update a line edit from the ViewModel without re-triggering its signals."""
    if edit.text() != text:
        with QSignalBlocker(edit):
            edit.setText(text)


class MainWindow(QMainWindow):
    def __init__(self, viewmodel: MainViewModel) -> None:
        super().__init__()
        self._vm = viewmodel
        self.setWindowTitle("Glint ✨ — Log Pattern Extraction")
        self.resize(1200, 780)

        self._build_ui()
        self._bind_viewmodel()
        self._apply_initial_state()

    # ================================================================== layout

    def _build_ui(self) -> None:
        central = QWidget(self)
        root = QVBoxLayout(central)

        # ---- Search configuration ----
        config_box = QGroupBox("Search configuration")
        form = QFormLayout(config_box)
        form.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        self.patterns_edit = QLineEdit()
        self.patterns_edit.setPlaceholderText("Path to patterns.json")
        browse_patterns = self._browse_button(self._browse_patterns_config)
        form.addRow("Patterns config:", self._row(self.patterns_edit, browse_patterns))

        self.pattern_combo = QComboBox()
        self.pattern_combo.setMinimumContentsLength(30)
        self.reload_button = QToolButton()
        self.reload_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_BrowserReload))
        self.reload_button.setToolTip("Reload patterns config")
        form.addRow("Pattern key:", self._row(self.pattern_combo, self.reload_button))

        self.columns_label = QLabel()
        self.columns_label.setWordWrap(True)
        self.columns_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.columns_label.setStyleSheet("color: palette(mid);")
        form.addRow("Columns:", self.columns_label)

        self.files_dir_edit = QLineEdit()
        self.files_dir_edit.setPlaceholderText("Directory containing the log files")
        form.addRow(
            "Log directory:",
            self._row(self.files_dir_edit, self._browse_button(self._browse_files_directory)),
        )

        self.file_pattern_edit = QLineEdit()
        self.file_pattern_edit.setPlaceholderText("Glob, e.g. *.log or server_*.txt")
        form.addRow("File pattern:", self.file_pattern_edit)

        self.keyword_edit = QLineEdit()
        self.keyword_edit.setPlaceholderText("Optional: only events containing this text (case-insensitive)")
        self.keyword_edit.setClearButtonEnabled(True)
        form.addRow("Event keyword:", self.keyword_edit)

        self.output_dir_edit = QLineEdit()
        self.output_dir_edit.setPlaceholderText("Directory for CSV / Excel reports")
        form.addRow(
            "Output directory:",
            self._row(self.output_dir_edit, self._browse_button(self._browse_output_directory)),
        )

        self.excel_check = QCheckBox("Also export to Excel (.xlsx)")
        form.addRow("", self.excel_check)

        # ---- Run controls ----
        controls = QHBoxLayout()
        self.start_button = QPushButton("Start search")
        self.start_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaPlay))
        self.start_button.setDefault(True)
        self.start_button.setMinimumWidth(140)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_MediaStop))
        self.open_folder_button = QPushButton("Open output folder")
        self.open_folder_button.setIcon(self.style().standardIcon(QStyle.StandardPixmap.SP_DirOpenIcon))
        self.open_csv_button = QPushButton("Open CSV")
        self.open_excel_button = QPushButton("Open Excel")

        self.validation_label = QLabel()
        self.validation_label.setStyleSheet("color: #d13438;")

        controls.addWidget(self.start_button)
        controls.addWidget(self.cancel_button)
        controls.addWidget(self.validation_label, 1)
        controls.addWidget(self.open_csv_button)
        controls.addWidget(self.open_excel_button)
        controls.addWidget(self.open_folder_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, PROGRESS_MAX)
        self.progress_bar.setFormat("%p%")

        # ---- Results / log tabs ----
        self.results_view = QTableView()
        self.results_view.setModel(self._vm.results_model)
        self.results_view.setAlternatingRowColors(True)
        self.results_view.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.results_view.setWordWrap(False)
        self.results_view.verticalHeader().setDefaultSectionSize(22)
        header = self.results_view.horizontalHeader()
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setDefaultSectionSize(180)
        header.setStretchLastSection(True)

        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumBlockCount(5000)
        mono = QFont("Consolas")
        mono.setStyleHint(QFont.StyleHint.Monospace)
        self.log_view.setFont(mono)

        self.tabs = QTabWidget()
        self.tabs.addTab(self.results_view, "Results preview")
        self.tabs.addTab(self.log_view, "Log")

        top = QWidget()
        top_layout = QVBoxLayout(top)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.addWidget(config_box)
        top_layout.addLayout(controls)
        top_layout.addWidget(self.progress_bar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.addWidget(top)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setChildrenCollapsible(False)

        root.addWidget(splitter)
        self.setCentralWidget(central)

        self.status_label = QLabel()
        status_bar = QStatusBar()
        status_bar.addWidget(self.status_label, 1)
        self.setStatusBar(status_bar)

    @staticmethod
    def _row(*widgets: QWidget) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        for index, widget in enumerate(widgets):
            layout.addWidget(widget, 1 if index == 0 else 0)
        return container

    def _browse_button(self, handler) -> QPushButton:
        button = QPushButton("Browse…")
        button.clicked.connect(handler)
        return button

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
        self.excel_check.toggled.connect(vm.set_export_excel)
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
        vm.can_start_changed.connect(self.start_button.setEnabled)
        vm.validation_message_changed.connect(self.validation_label.setText)
        vm.running_changed.connect(self._on_running_changed)
        vm.progress_changed.connect(self.progress_bar.setValue)
        vm.progress_busy_changed.connect(self._set_progress_busy)
        vm.status_text_changed.connect(self.status_label.setText)
        vm.log_message.connect(self._append_log)
        vm.search_finished.connect(self._on_search_finished)

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
        self.start_button.setEnabled(vm.can_start)
        self.validation_label.setText(vm.validation_message)
        self.status_label.setText(vm.status_text)
        self._on_running_changed(vm.is_running)
        self._update_result_buttons(vm.last_result)

    # ============================================================ VM -> View

    def _set_excel_checked(self, checked: bool) -> None:
        with QSignalBlocker(self.excel_check):
            self.excel_check.setChecked(checked)

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
        self.columns_label.setText(", ".join(columns) if columns else "—")

    def _on_running_changed(self, running: bool) -> None:
        for widget in (
            self.patterns_edit,
            self.pattern_combo,
            self.reload_button,
            self.files_dir_edit,
            self.file_pattern_edit,
            self.keyword_edit,
            self.output_dir_edit,
            self.excel_check,
        ):
            widget.setEnabled(not running)
        self.cancel_button.setEnabled(running)
        self.start_button.setEnabled(self._vm.can_start)
        if running:
            self._update_result_buttons(None)
            self.tabs.setCurrentWidget(self.results_view)

    def _set_progress_busy(self, busy: bool) -> None:
        if busy:
            self.progress_bar.setRange(0, 0)
        else:
            self.progress_bar.setRange(0, PROGRESS_MAX)

    def _append_log(self, level: int, message: str) -> None:
        cursor = self.log_view.textCursor()
        cursor.movePosition(cursor.MoveOperation.End)
        fmt = QTextCharFormat()
        color = _LOG_COLORS.get(level)
        if color is not None:
            fmt.setForeground(color)
        if self.log_view.document().isEmpty():
            cursor.insertText(message, fmt)
        else:
            cursor.insertBlock()
            cursor.insertText(message, fmt)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def _on_search_finished(self, result: SearchResult) -> None:
        self._update_result_buttons(result)
        if result.status is SearchStatus.FAILED:
            self.tabs.setCurrentWidget(self.log_view)
        elif result.status is SearchStatus.COMPLETED:
            self.results_view.resizeColumnsToContents()
            header = self.results_view.horizontalHeader()
            for col in range(header.count()):
                header.resizeSection(col, min(header.sectionSize(col), 400))

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
