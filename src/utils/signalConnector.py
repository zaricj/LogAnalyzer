"""Centralized signal connection management."""

from typing import TYPE_CHECKING
from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QPixmap, QIcon, QDesktopServices
from PySide6.QtCore import Slot, QSettings, QUrl

if TYPE_CHECKING:
    from app import MainWindow
    from core.exportManager import ExportManager
    from core.fileParser import FileParserWorker


class SignalConnector:
    """Manages signal connections for worker threads."""

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.ui = main_window.ui

    def connect_export_manager_signals(self, worker: "ExportManager"):
        """Connect signals for XML parsing operations."""
        worker.signals.statusbar_message.connect(self.handle_statusbar_show_message)
        worker.signals.export_success.connect(self.handle_export_manager_success)

    def connect_file_parser_worker(self, worker: "FileParserWorker"):
        """Connect signals for file parsing operations."""
        worker.signals.output_text_edit_append.connect(self.handle_text_edit_append)

    # ====== Slots ====== #

    @Slot(str, int)
    def handle_statusbar_show_message(self, message: str, duration: int) -> None:
        """Handler for QStatusbar showMessage signals.

        Args:
            message (str): The message to be shown in the statusbar.
            duration (int): The duration of the message in milliseconds.
        """
        self.ui.statusbar.showMessage(message, duration)

    @Slot(str)
    def handle_text_edit_append(self, message: str) -> None:
        """Handler for QTextEdit append signals.

        Args:
            message (str): The message to display in the QTextEdit.
        """

        self.ui.text_edit_program_output.append(message)

    @Slot(str, str, str, str)
    def handle_export_manager_success(
        self, title: str, message: str, save_as_path: str, app_icon_path: str
    ):
        """Enhanced success handler with 'Open Folder' button"""

        app_icon = QIcon(app_icon_path)
        app_icon_as_pixmap = QPixmap(app_icon_path)

        msg_box = QMessageBox()
        msg_box.setIconPixmap(app_icon_as_pixmap)
        msg_box.setWindowIcon(app_icon)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)
        msg_box.setInformativeText(f"File saved to:\n{save_as_path}")

        # Add custom buttons
        open_folder_btn = msg_box.addButton(
            "Open Folder", QMessageBox.ButtonRole.ActionRole
        )
        open_file_btn = msg_box.addButton(
            "Open File", QMessageBox.ButtonRole.ActionRole
        )
        ok_btn = msg_box.addButton(QMessageBox.StandardButton.Ok)

        # Set OK as default
        msg_box.setDefaultButton(ok_btn)

        # Execute dialog and handle response
        msg_box.exec()

        clicked_button = msg_box.clickedButton()

        if clicked_button == open_folder_btn:
            # Open the folder containing the file
            folder_path = str(Path(save_as_path).parent)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
        elif clicked_button == open_file_btn:
            # Open the file directly
            QDesktopServices.openUrl(QUrl.fromLocalFile(save_as_path))
