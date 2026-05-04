from PySide6.QtWidgets import QFileSystemModel, QLineEdit, QComboBox
from PySide6.QtCore import QModelIndex, QStandardPaths, Slot

from typing import TYPE_CHECKING
from pathlib import Path

from datetime import datetime
import re

from gui.thread_worker import Worker

if TYPE_CHECKING:
    from app import MainWindow


class DirectoryViewer:

    def __init__(self, main_window: "MainWindow", start_path=None):
        self.main_window = main_window
        self.ui = main_window.ui
        self.start_path = start_path
        self._active_preview_worker: Worker | None = None
        self._pending_preview_path: str | None = None
        self._current_preview_content: str = ""

        # 1. Setup the Model
        self.model = QFileSystemModel()

        # Set the root path for the model
        if self.start_path is None:
            # Default to the user's home directory if no path is provided
            # You can specify a starting path, e.g., 'C:/' on Windows or '/home/user/' on Linux
            # QStandardPaths.writableLocation(QStandardPaths.StandardLocation.HomeLocation)
            self.start_path = QStandardPaths.writableLocation(
                QStandardPaths.StandardLocation.HomeLocation
            )
        else:
            self.start_path = str(self.start_path)

        # Set the root path on the model
        self.model.setRootPath(self.start_path)

        # 2. Setup the View
        self.ui.treeview_directory_view.setModel(self.model)

        # Set the view's root index to display the contents of the starting path
        # If you want to show the full drive structure, setRootPath is enough,
        # but to limit the view to a specific folder's contents, set setRootIndex.
        root_index = self.model.index(self.start_path)
        self.ui.treeview_directory_view.setRootIndex(root_index)

        # Optional: Configure the view appearance
        self.ui.treeview_directory_view.setSortingEnabled(True)
        self.ui.treeview_directory_view.setHeaderHidden(False)

        # Optionally hide columns you don't need (e.g., size, type, date)
        # 0: Name, 1: Size, 2: Type, 3: Date Modified
        self.ui.treeview_directory_view.setColumnHidden(1, False)  # Show Size
        self.ui.treeview_directory_view.setColumnHidden(2, True)  # Hide Type
        self.ui.treeview_directory_view.setColumnHidden(3, False)  # Hide Date Modified

        # Expand column 'Name'
        self.ui.treeview_directory_view.setColumnWidth(0, 200)

        # Connect the selection signal to a handler
        self.ui.treeview_directory_view.clicked.connect(self.on_item_clicked)

    def check_if_file_or_folder(self, path: str) -> str:
        """
        Checks if the given path is a file or folder.
        Returns "file", "folder", or "not found".
        """
        p = Path(path)
        if p.is_file():
            return "file"
        elif p.is_dir():
            return "folder"
        else:
            return "not found"

    def set_root_path(self, path: str):
        """
        Sets the root path for the directory viewer to display the contents of the given path.
        """
        self.model.setRootPath(path)
        root_index = self.model.index(path)
        self.ui.treeview_directory_view.setRootIndex(root_index)

    def on_item_clicked(self, index: QModelIndex):
        """
        Handles an item being clicked in the QTreeView.
        """
        # Get the absolute file path from the model for the given index
        file_path: str = self.model.filePath(index)
        # Init the line edit where to set the path
        line_edit: QLineEdit = self.ui.input_browse_folder
        check: str = self.check_if_file_or_folder(file_path)

        if check == "folder":
            self.set_folder_path(line_edit, file_path)  # Set file path in the line edit
        elif check == "file":
            self.load_file_preview(file_path)
        else:
            self.ui.text_edit_log_preview.setPlainText(f"Path not found:\n{file_path}")
            self.ui.statusbar.showMessage("Unable to load selected path.", 5000)

    def load_file_preview(self, file_path: str) -> None:
        self._pending_preview_path = file_path
        self._current_preview_content = ""
        self.ui.text_edit_log_preview.setPlainText(
            f"Loading file preview...\n{file_path}"
        )
        self.ui.combobox_time.clear()
        max_bytes = self.set_max_filesize_preview(file_path)

        worker = Worker(
            self.read_file_preview_content, file_path, max_bytes
        )
        worker.signals.result.connect(self.on_file_preview_result)
        worker.signals.error.connect(self.on_file_preview_error)
        worker.signals.finished.connect(self.on_file_preview_finished)
        self._active_preview_worker = worker
        self.main_window.thread_pool.start(worker)
        
    def set_max_filesize_preview(self, file_path: str) -> int:
        """Set the max file size to preview

        Returns:
            int: The number of bytes to preview.
        """
        # Truncate only when checkbox is checked.
        if self.ui.checkbox_truncate_preview.isChecked():
            # Get the spinbox value
            max_bytes = self.ui.spinbox_max_filesize_preview.value() * 1024
        else:
            max_bytes = Path(file_path).stat().st_size

        return max_bytes

    def set_folder_path(self, line_edit: QLineEdit, text_to_display: str = None):
        """
        Sets the selected item's path into the provided QLineEdit.
        """
        line_edit.setText(text_to_display)

    def read_file_preview_content(self, file_path: str, max_bytes: int) -> dict:
        file = Path(file_path)
        with file.open("rb") as handle:
            payload = handle.read(max_bytes + 1)
            payload = payload[:max_bytes]

        text = payload.decode("utf-8", errors="replace")
        date_time_values = self.extract_dates_from_content(text)

        return {
            "path": str(file),
            "content": text,
            "date_time_values": date_time_values,
        }

    def populate_date_time_combobox(
        self, file_content: str, combobox: QComboBox, date_time_values: list[str] | None = None
    ) -> None:
        if len(file_content) == 0:
            self.ui.statusbar.showMessage(
                "No file context found in the text area.", 10000
            )
            combobox.clear()
            return

        if date_time_values is None:
            date_time_values = self.extract_dates_from_content(file_content)
        combobox.blockSignals(True)
        combobox.clear()
        combobox.addItem("All")
        if date_time_values:
            combobox.addItems(date_time_values)
        combobox.setCurrentIndex(0)
        combobox.blockSignals(False)

        if not date_time_values:
            self.ui.statusbar.showMessage("No date or time like formats found.", 10000)

    def extract_dates_from_content(self, file_content):
        try:
            # Split the log content into lines
            lines = file_content.splitlines()

            # Define possible date patterns with strict and specific matching
            date_patterns = [
                (r"^(\d{2}\.\d{2}\.\d{4})", "%d.%m.%Y"),  # DD.MM.YYYY
                (r"^(\d{2}-\d{2}-\d{4})", "%d-%m-%Y"),  # DD-MM-YYYY
                (r"^(\d{2}\.\d{2}\.\d{2})", "%d.%m.%y"),  # DD.MM.YY
                (r"^(\d{2}-\d{2}-\d{2})", "%d-%m-%y"),  # DD-MM-YY
                (r"^(\d{2}:\d{2}:\d{2})", "%H:%M:%S"),  # H:M:S
            ]

            dates = set()  # Use a set to store unique dates

            # Process each line
            for line in lines:
                # Extract the first 10 characters of the line
                first_10_chars = line[:10]

                # Try to match each pattern
                for pattern, date_format in date_patterns:
                    match = re.match(pattern, first_10_chars)
                    if match:
                        date_str = match.group(1)
                        try:
                            # Validate the date by parsing it
                            datetime.strptime(date_str, date_format)
                            dates.add(
                                (date_str, date_format)
                            )  # Store date and its format
                            break  # Stop checking other patterns once a match is found
                        except ValueError:
                            # If the date is invalid (e.g., 30.02.2023), skip it
                            continue

            if not dates:
                raise ValueError("No valid date patterns found in the log file.")

            # Convert matched dates to datetime objects
            dates_datetime = []
            for date_str, date_format in dates:
                dates_datetime.append(datetime.strptime(date_str, date_format))

            # Sort the datetime objects
            dates_datetime_sorted = sorted(dates_datetime)

            # Convert datetime objects back to strings using their original format
            dates_sorted = []
            for date in dates_datetime_sorted:
                # Find the original format for this date
                for date_str, date_format in dates:
                    if datetime.strptime(date_str, date_format) == date:
                        dates_sorted.append(date.strftime(date_format))
                        break

            return dates_sorted

        except Exception as ex:
            return []

    @Slot(object)
    def on_file_preview_result(self, result: object) -> None:
        if not isinstance(result, dict):
            self._current_preview_content = ""
            self.ui.combobox_time.clear()
            self.ui.text_edit_log_preview.setPlainText("Failed to render preview.")
            return

        path = str(result.get("path", ""))
        if not path:
            return
        if self._pending_preview_path and Path(path) != Path(self._pending_preview_path):
            return

        preview_content = str(result.get("content", ""))
        date_time_values = result.get("date_time_values", [])
        if not isinstance(date_time_values, list):
            date_time_values = []
        self._current_preview_content = preview_content

        self.ui.text_edit_log_preview.setPlainText(preview_content)
        self.populate_date_time_combobox(
            self._current_preview_content,
            self.ui.combobox_time,
            date_time_values,
        )
        self.ui.statusbar.showMessage(f"Loaded preview: {path}", 5000)

    @Slot(tuple)
    def on_file_preview_error(self, error_data: tuple) -> None:
        _exctype, value, _traceback_text = error_data
        path = self._pending_preview_path or ""
        self._current_preview_content = ""
        self.ui.combobox_time.clear()
        self.ui.text_edit_log_preview.setPlainText(
            f"Failed to load file preview:\n{path}\n\n{value}"
        )
        self.ui.statusbar.showMessage("File preview failed to load.", 5000)

    @Slot()
    def on_file_preview_finished(self) -> None:
        self._active_preview_worker = None

    def get_current_preview_content(self) -> str:
        return self._current_preview_content
