from PySide6.QtWidgets import QMessageBox, QFileDialog, QLineEdit, QStatusBar
from PySide6.QtGui import QDesktopServices
from PySide6.QtCore import QUrl
from typing import TYPE_CHECKING
from pathlib import Path
import os
import sys
import subprocess

if TYPE_CHECKING:
    from app import MainWindow


class HelperMethods:
    def __init__(self, main_window: "MainWindow"):
        """Accepts a reference to the main window so dialogs have a valid parent."""
        self.main_window = main_window
        self.ui = self.main_window.ui

    def open_folder_in_file_explorer(self, folder_path: str):
        """Helper method to open folder in file explorer."""
        if folder_path and os.path.exists(folder_path):
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(folder_path))
            except Exception as ex:
                message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
                QMessageBox.critical(self.main_window, "An exception occurred", message)
        else:
            self.ui.text_edit_program_output.setText(
                f"Invalid or missing path: Could not open directory: {folder_path}"
            )

    def open_file_directly(self, file_path: str):
        """Helper method to open file in default application."""
        if file_path and os.path.exists(file_path):
            try:
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            except Exception as ex:
                message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
                QMessageBox.critical(self.main_window, "An exception occurred", message)
        else:
            self.ui.text_edit_program_output.setText(
                f"Invalid or missing path: Could not open file: {file_path}"
            )

    def browse_folder_helper(self, dialog_message: str, line_widget: QLineEdit):
        """Helper for folder browsing dialogs."""
        try:
            input_text = line_widget.text()
            if len(input_text) > 0:
                folder = QFileDialog.getExistingDirectory(
                    self.main_window, dialog_message, input_text
                )
            else:
                folder = QFileDialog.getExistingDirectory(
                    self.main_window, dialog_message
                )
            if folder:
                line_widget.setText(folder)
                self.main_window.dir_viewer.set_root_path(
                    folder
                )  # Set the directory viewer path
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(
                self.main_window,
                "An exception occurred in browse folder method",
                message,
            )

    def browse_file_helper_non_input(
        self, dialog_message: str, file_extension_filter: str
    ) -> str:
        """Helper for file browsing dialogs.

        Returns:
            Path of selected file as string.
        """
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self.main_window, caption=dialog_message, filter=file_extension_filter
            )
            if file_name:
                return file_name
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(
                self.main_window,
                "An exception occurred in browse file method",
                message,
            )

    def browse_file_helper(
        self, dialog_message: str, line_widget: QLineEdit, file_extension_filter: str
    ):
        """Helper for file browsing dialogs."""
        try:
            file_name, _ = QFileDialog.getOpenFileName(
                self.main_window, caption=dialog_message, filter=file_extension_filter
            )
            if file_name:
                line_widget.setText(file_name)
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(
                self.main_window,
                "An exception occurred in browse file method",
                message,
            )

    def browse_save_file_as_helper(
        self,
        dialog_message: str = "Save File As",
        statusbar_widget: QStatusBar = None,
        line_widget: QLineEdit = None,
        file_extension_filter: str = "",
        filename_placeholder: str = "",
    ) -> str:
        """Helper for save file dialogs.

        Args:
            dialog_message (str, optional): Message for the save file dialog.. Defaults to "Save File As".
            statusbar_widget (QStatusBar, optional): The status bar widget to show messages in. Defaults to None.
            line_widget (QLineEdit, optional): The line edit widget to update with the file path. Defaults to None.
            file_extension_filter (str, optional): File extension filter for the dialog. Defaults to "".
            filename_placeholder (str, optional): Placeholder filename for the dialog. Defaults to "".

        Returns:
            file_path (str): The selected file path
        """
        try:
            file_name, _ = QFileDialog.getSaveFileName(
                self.main_window,
                caption=dialog_message,
                dir=filename_placeholder,
                filter=file_extension_filter,
            )
            if file_name:
                if line_widget is not None:
                    line_widget.setText(file_name)
                    if statusbar_widget is not None:
                        statusbar_widget.showMessage(
                            f"File saved as: {file_name}", 5000
                        )
                else:
                    if statusbar_widget is not None:
                        statusbar_widget.showMessage(
                            f"File saved as: {file_name}", 5000
                        )

                return file_name
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(
                self.main_window,
                "An exception occurred in browse save file method",
                message,
            )

    def open_dir_in_file_manager(self, folder_path: Path | str) -> None:
        """Opens the specified folder path in the file system manager. OS cross-platform independent, support Windows, Linux and macOS.

        Args:
            folder_path (str): Folder path to open in the file system manager.
        """
        try:
            if folder_path != "":
                path = Path(folder_path)
                if sys.platform == "win32":
                    os.startfile(path)
                else:
                    opener = "open" if sys.platform == "darwin" else "xdg-open"
                    subprocess.call([opener, path])
            else:
                self.ui.statusbar.showMessage(
                    "Please set the folder path in the specific input field first!",
                    6000,
                )
        except Exception as ex:
            msg: str = f"Exception {type(ex).__name__}, could not open directory in file system manager, error message: {str(ex)}"
            self.ui.statusbar.showMessage(msg)
