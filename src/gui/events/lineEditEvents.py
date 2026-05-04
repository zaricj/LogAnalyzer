from PySide6.QtCore import Slot
from PySide6.QtWidgets import QLineEdit, QMessageBox
from typing import TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from app import MainWindow


class LineEditHandler:
    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.ui = main_window.ui

    def connect_signals(self):
        """Connect all line edit events to their handlers."""
        # Input field for searching specific file patterns
        self.ui.input_file_pattern.textChanged.connect(
            lambda: self.set_file_pattern(self.ui.input_browse_folder.text())
        )
        self.ui.input_filter_table.textChanged.connect(self.on_filter_table)

    @Slot(str)
    def set_file_pattern(self, folder_path: str) -> None:
        """Prints out the relevant info based on browse button press or just text changed in the specified input field

        Args:
            folder_path (str): Path of the folder which is grabbed from the QFileDialog window.
        """
        input_field_text: str = self.ui.input_file_pattern.text()
        path: Path = Path(folder_path)

        if path.exists() and path.is_dir() and input_field_text != ".":
            files = []
            file_patterns = input_field_text.strip().split(",")
            # Fixed: Check if file_patterns is not empty and contains valid patterns
            if file_patterns and file_patterns != [""]:
                self.ui.text_edit_program_output.setText(
                    f"Using file patterns: {file_patterns}"
                )

                for pattern in file_patterns:
                    pattern = pattern.strip()
                    if pattern:
                        files.extend(path.glob(pattern))
                        self.ui.text_edit_program_output.setText(
                            f"Pattern '{pattern}' matched {len(list(path.glob(pattern)))} files."
                        )
                if len(files) > 0:
                    self.ui.statusbar.showMessage(
                        f"Selected folder: {folder_path} | Total files: {len(files)} | Using patterns: {file_patterns}",
                        10000,
                    )
            else:
                files = list(path.glob("*.*"))
                if len(files) > 0:
                    self.ui.statusbar.showMessage(
                        f"Selected folder: {folder_path} | Total files: {len(files)}",
                        10000,
                    )

    @Slot(str)
    def on_filter_table(self, text: str):
        """Filter QTableView rows based on the search text."""
        text = text.strip().lower()
        model = self.ui.table_view_result.model()  # Get the tables model
        if model is None:
            return
        row_count = model.rowCount()  # Count rows of table via the acquired model
        column_count = model.columnCount()  # Count columns of table
        for row in range(row_count):
            row_match = False
            for col in range(column_count):
                item: str = model.index(row, col).data()
                if item and text in item.lower():
                    row_match = True
                    break

            self.ui.table_view_result.setRowHidden(row, not row_match)
