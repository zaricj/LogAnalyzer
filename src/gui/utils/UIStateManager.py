"""Service for managing UI state and widget states."""

from ast import List
from typing import TYPE_CHECKING
from PySide6.QtWidgets import QWidget

if TYPE_CHECKING:
    from app import MainWindow


class UIStateManager:
    """
    Manages UI widget states (enabled/disabled, visible/hidden).
    Centralizes UI state management logic for better separation of concerns.
    """

    def __init__(self, main_window: "MainWindow"):
        self.main_window = main_window
        self.ui = main_window.ui

    def initial_ui_state_on_start(self) -> None:
        """Initialize the ui state on startup. Disable/hide some ui widgets/elements."""
        # Disable buttons, radios and progressbar associated with Table Widget
        self.ui.button_clear_table.setEnabled(False)
        self.ui.button_export.setEnabled(False)
        self.ui.radiobutton_csv.setEnabled(False)
        self.ui.radiobutton_excel.setEnabled(False)
        self.ui.progressbar.setVisible(False)

    def enable_widgets(self, widgets: list[QWidget]) -> None:
        """Enables the given PySide6 widgets as a list

        Args:
            widgets (list[QWidget]): List of widgets to enable with .setEnabled(True)
        """
        for widget in widgets:
            widget.setEnabled(True)

    def disable_widgets(self, widgets: list[QWidget]) -> None:
        """Disable the given PySide6 widgets as a list

        Args:
            widgets (list[QWidget]): List of widgets to disable with .setEnabled(False)
        """
        for widget in widgets:
            widget.setEnabled(False)

    def hide_widgets(self, widgets: list[QWidget]) -> None:
        """Hides the given PySide6 widgets as a list

        Args:
            widgets (list[QWidget]): List of widgets to hide with .setVisible(False)
        """
        for widget in widgets:
            widget.setVisible(False)

    def show_widgets(self, widgets: list[QWidget]) -> None:
        """Unhides the given PySide6 widgets as a list

        Args:
            widgets (list[QWidget]): List of widgets to unhide with .setVisible(True)
        """
        for widget in widgets:
            widget.setVisible(True)
