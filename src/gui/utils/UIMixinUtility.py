from pathlib import Path
from PySide6.QtWidgets import QMessageBox
from PySide6.QtGui import QIcon
from PySide6.QtCore import Slot, QSettings

from gui.LobsterGeneralLogViewer_ui import Ui_MainWindow
from gui.widgets.treeViewModel import DirectoryViewer
from gui.widgets.tableViewModel import ResultsTableWidget

# Path configuration (for pattern handler mainly)
FILE_DIR = Path(__file__).resolve()
ROOT_DIR = FILE_DIR.parents[2]  # src Folder
CONFIG_DIRECTORY: Path = ROOT_DIR / "config"
LOG_PATTERN_CONFIG: Path = CONFIG_DIRECTORY / "log_patterns.json"
GUI_SETTINGS_CONFIG: Path = CONFIG_DIRECTORY / "gui_settings.json"


class Mixin:
    """
    Mixin class that provides signal handling interface using specialized handlers.
    Delegates responsibilities to focused handler classes for better separation of concerns.
    """

    # Type hints for attributes accessed in this mixin
    ui: Ui_MainWindow
    # helper: 'HelperMethods'
    # ui_state_manager: 'UIStateManager'
    settings: "QSettings"
    set_max_threads: int

    def initialize_ui_all(self):
        """Initialize all utilities, handlers, ui signals etc..."""
        self.initialize_views()  # Initialize all the different views like Table and Tree
        self.initialize_utilities()  # Initialize utilities first
        self.initialize_handlers()  # Then handlers (which depend on utilities)
        self.initialize_handler_signals()  # Finally connect signals

    def initialize_handlers(self):
        """Initialize all specialized event handlers."""
        from gui.events.buttonEvents import ButtonEventHandler
        from gui.events.comboboxEvents import ComboBoxEventHandler
        from gui.events.lineEditEvents import LineEditHandler
        from gui.events.menuBarEvents import MenuBarHandler
        from gui.events.checkboxEvents import CheckboxHandler

        self.button_handler = ButtonEventHandler(self)
        self.combobox_handler = ComboBoxEventHandler(self)
        self.line_edit_handler = LineEditHandler(self)
        self.checkbox_handler = CheckboxHandler(self)
        self.menu_bar_handler = MenuBarHandler(self)

    def initialize_handler_signals(self):
        self.button_handler.connect_signals()
        self.combobox_handler.connect_signals()
        self.line_edit_handler.connect_signals()
        self.checkbox_handler.connect_signals()
        self.menu_bar_handler.connect_signals()

    def initialize_utilities(self):
        from gui.utils.UIStateManager import UIStateManager
        from gui.utils.helperUtility import HelperMethods
        from gui.utils.configHandler import ConfigHandler

        self.helper = HelperMethods(self)
        self.ui_state_manager = UIStateManager(self)
        self.log_pattern_handler = ConfigHandler(
            self, CONFIG_DIRECTORY, LOG_PATTERN_CONFIG
        )

    def initialize_views(self):
        # Init the tree view model object
        self.dir_viewer = DirectoryViewer(self)
        self.table_results = ResultsTableWidget(self)

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
