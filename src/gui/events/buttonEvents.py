from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from PySide6.QtCore import Slot
from PySide6.QtWidgets import QMessageBox, QTextEdit

from core.exporter import export_to_csv, export_to_excel
from gui.thread_worker import Worker
from gui.widgets.tableViewModel import ResultsTableWidget
from services.log_service import LogService, ParseLogsResult

if TYPE_CHECKING:
    from app import MainWindow


class ButtonEventHandler:
    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.ui = main_window.ui

        self.log_service = LogService(self.main_window.log_pattern_config)
        self._active_worker: Worker | None = None

    def connect_signals(self):
        """Connect all button events to their handlers."""
        self.ui.button_browse_folder.clicked.connect(
            lambda: self.main_window.helper.browse_folder_helper(
                "Browse folder",
                self.ui.input_browse_folder,
            )
        )
        self.ui.button_import_csv.clicked.connect(self.on_load_csv_file_for_table)
        self.ui.button_clear_table.clicked.connect(self.on_clear_table)
        self.ui.button_parse_files.clicked.connect(self.on_parse_files)
        self.ui.button_export.clicked.connect(self.on_export_data)
        self.ui.button_pattern_configuration_info.clicked.connect(self.on_pattern_config_info)

    @Slot()
    def on_pattern_config_info(self) -> None:
        output_widget: QTextEdit = self.ui.text_edit_program_output
        selected_key = self.ui.combobox_configuration.currentText()
        selected_data = self.main_window.log_pattern_handler.get(
            f"profiles.{selected_key}"
        )
        if not selected_data:
            selected_data = self.main_window.log_pattern_handler.get(selected_key)

        if not selected_data:
            output_widget.setText("No data available for selected configuration key.")
            return

        if isinstance(selected_data, dict):
            output_widget.setText("Key\tValue")
            for key, value in selected_data.items():
                output_widget.append(f"{key}   ----->   {value}")
            return

        output_widget.setText(f"Config value: {selected_data}")

    @Slot()
    def on_load_csv_file_for_table(self) -> None:
        try:
            file_path = self.main_window.helper.browse_file_helper_non_input(
                dialog_message="Select CSV file to display",
                file_extension_filter="CSV File (*.csv)",
            )
            if not file_path:
                return

            dataframe = pd.read_csv(file_path)
            self.populate_results_table(dataframe)
            self._set_table_action_widgets_enabled(True)
            self.ui.statusbar.showMessage(f"Loaded CSV file: {file_path}", 10000)
        except Exception as ex:
            QMessageBox.critical(
                self.main_window,
                "CSV Load Error",
                f"{type(ex).__name__}: {ex}",
            )

    @Slot()
    def on_parse_files(self) -> None:
        folder_path_raw = self.ui.input_browse_folder.text().strip()
        if not folder_path_raw:
            QMessageBox.warning(
                self.main_window, "Parse Logs", "Please select a folder first."
            )
            return

        folder_path = Path(folder_path_raw)
        if not folder_path.exists() or not folder_path.is_dir():
            QMessageBox.warning(
                self.main_window,
                "Parse Logs",
                f"Invalid folder: {folder_path}",
            )
            return

        file_patterns = self._parse_file_patterns(self.ui.input_file_pattern.text())
        selected_profile = self.ui.combobox_configuration.currentText().strip() or None

        self.ui.progressbar.setVisible(True)
        self.ui.progressbar.setRange(0, 100)
        self.ui.progressbar.setValue(0)
        self.ui.button_parse_files.setEnabled(False)
        self.ui.statusbar.showMessage("Parsing log files...", 5000)

        worker = Worker(
            self.log_service.parse_folder,
            folder_path,
            file_patterns,
            selected_profile,
        )
        worker.signals.progress.connect(self.on_parse_progress)
        worker.signals.result.connect(self.on_parse_result)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.finished.connect(self.on_parse_finished)

        self._active_worker = worker
        self.main_window.thread_pool.start(worker)

    @Slot(int)
    def on_parse_progress(self, progress: int) -> None:
        self.ui.progressbar.setValue(progress)
        self.ui.statusbar.showMessage(f"Parsing logs... {progress}%", 1000)

    @Slot(object)
    def on_parse_result(self, result: ParseLogsResult) -> None:
        self.populate_results_table(result.dataframe)
        has_data = not result.dataframe.empty
        self._set_table_action_widgets_enabled(has_data)
        self._render_parse_summary(result)

        self.ui.statusbar.showMessage(
            "Parsing completed. "
            f"Profile: {result.pattern_profile} | "
            f"Files: {result.files_processed} | "
            f"Entries: {result.summary.get('total_entries', 0)}",
            10000,
        )

    @Slot()
    def on_parse_finished(self) -> None:
        self.ui.button_parse_files.setEnabled(True)
        self.ui.progressbar.setVisible(False)
        self._active_worker = None

    @Slot()
    def on_clear_table(self) -> None:
        self.ui.table_view_result.setModel(None)
        self.ui.input_filter_table.clear()
        self._set_table_action_widgets_enabled(False)
        self.ui.statusbar.showMessage("Cleared table data.", 5000)

    def on_export_data(self) -> None:
        dataframe = self._get_current_dataframe()
        if dataframe is None or dataframe.empty:
            QMessageBox.warning(self.main_window, "Export", "No data to export.")
            return

        csv_checked = self.ui.radiobutton_csv.isChecked()
        excel_checked = self.ui.radiobutton_excel.isChecked()

        if not csv_checked and not excel_checked:
            QMessageBox.warning(
                self.main_window, "Export", "Please select CSV or Excel."
            )
            return

        if csv_checked:
            save_as_path = self.main_window.helper.browse_save_file_as_helper(
                dialog_message="Save CSV file",
                file_extension_filter="CSV File (*.csv)",
                statusbar_widget=self.ui.statusbar,
            )
            if not save_as_path:
                return
            worker = Worker(export_to_csv, dataframe.copy(), save_as_path, ";")
        else:
            save_as_path = self.main_window.helper.browse_save_file_as_helper(
                dialog_message="Save Excel file",
                file_extension_filter="Excel File (*.xlsx)",
                statusbar_widget=self.ui.statusbar,
            )
            if not save_as_path:
                return
            worker = Worker(export_to_excel, dataframe.copy(), save_as_path)

        self.ui.button_export.setEnabled(False)  # Disable the export button
        worker.signals.result.connect(self.on_export_success)
        worker.signals.error.connect(self.on_worker_error)
        worker.signals.finished.connect(self.on_export_finished)
        self._active_worker = worker
        self.main_window.thread_pool.start(worker)

    @Slot(object)
    def on_export_success(self, output_path: object) -> None:
        self.ui.statusbar.showMessage(f"Export completed: {output_path}", 10000)

    @Slot()
    def on_export_finished(self) -> None:
        self.ui.button_export.setEnabled(True)
        self._active_worker = None

    @Slot(tuple)
    def on_worker_error(self, error_data: tuple) -> None:
        _exctype, value, traceback_text = error_data
        QMessageBox.critical(
            self.main_window, "Background Task Error", f"{value}\n\n{traceback_text}"
        )
        self.ui.statusbar.showMessage("Background task failed.", 10000)

    @Slot(pd.DataFrame)
    def populate_results_table(self, data: pd.DataFrame) -> None:
        if data.empty:
            self.ui.table_view_result.setModel(None)
            return

        model = ResultsTableWidget(data)
        self.ui.table_view_result.setModel(model)
        self.ui.table_view_result.resizeColumnsToContents()
        self.ui.table_view_result.setSortingEnabled(
            False
        )  # Disable sorting via headers/columns

    def _render_parse_summary(self, result: ParseLogsResult) -> None:
        output = self.ui.text_edit_program_output
        output.clear()  # Clear text area
        output.append(f"Pattern profile: {result.pattern_profile}")
        output.append(f"Processed files: {result.files_processed}")
        output.append(f"Parsed entries: {result.summary.get('total_entries', 0)}")

        exception_counts = result.summary.get("exceptions", {})
        if isinstance(exception_counts, dict) and exception_counts:
            output.append("Exception summary:")
            for key, count in sorted(
                exception_counts.items(), key=lambda item: item[1], reverse=True
            ):
                output.append(f"  {key}: {count}")

    def _get_current_dataframe(self) -> pd.DataFrame | None:
        model = self.ui.table_view_result.model()
        if not isinstance(model, ResultsTableWidget):
            return None
        return model.dataframe

    def _set_table_action_widgets_enabled(self, enabled: bool) -> None:
        widgets = [
            self.ui.button_clear_table,
            self.ui.button_export,
            self.ui.radiobutton_csv,
            self.ui.radiobutton_excel,
        ]
        if enabled:
            self.main_window.ui_state_manager.enable_widgets(widgets)
        else:
            self.main_window.ui_state_manager.disable_widgets(widgets)

    def _parse_file_patterns(self, text: str) -> list[str]:
        patterns = [pattern.strip() for pattern in text.split(",") if pattern.strip()]
        if not patterns:
            return ["*.log"]
        return patterns
