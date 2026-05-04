from pathlib import Path
from typing import Self
import sys
import qdarktheme

from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QSplitter

from PySide6.QtGui import QCloseEvent, QGuiApplication, QIcon
from PySide6.QtCore import QSettings, QThreadPool

from gui.LobsterGeneralLogViewer_ui import Ui_MainWindow
from gui.utils.UIMixinUtility import Mixin

# ----------------------------
# Constants
# ----------------------------
ROOT_DIR = Path(__file__).parent
APP_ICON: Path = ROOT_DIR / "gui" / "assets" / "icons" / "Geis.ico"

# Application versioning and metadata
APP_VERSION: str = "v1.0.0"
APP_NAME: str = "LobsterLogReporter"
AUTHOR: str = "Jovan"


# ----------------------------
# Helpers for window state
# ----------------------------
def save_window_state(window: QMainWindow, settings: QSettings):
    settings.setValue("geometry", window.saveGeometry())
    settings.setValue("windowState", window.saveState())


def restore_window_state(window: QMainWindow, settings: QSettings):
    geometry = settings.value("geometry")
    if geometry:
        window.restoreGeometry(geometry)
    state = settings.value("windowState")
    if state:
        window.restoreState(state)

    # Clamp window into current screen space
    screen = QGuiApplication.primaryScreen()
    available = screen.availableGeometry()
    win_geom = window.frameGeometry()

    if not available.contains(win_geom, proper=False):
        window.resize(
            min(win_geom.width(), available.width()),
            min(win_geom.height(), available.height()),
        )
        window.move(
            max(
                available.left(),
                min(win_geom.left(), available.right() - window.width()),
            ),
            max(
                available.top(),
                min(win_geom.top(), available.bottom() - window.height()),
            ),
        )


def save_splitter_state(
    splitter: QSplitter, settings: QSettings, key: str = "splitterState"
):
    settings.setValue(key, splitter.saveState())


def restore_splitter_state(
    splitter: QSplitter, settings: QSettings, key: str = "splitterState"
):
    state = settings.value(key)
    if state:
        splitter.restoreState(state)


def initialize_theme(
    parent: Self,
    theme: str,
    settings: QSettings,
    key: str = "appAppearanceMode"):
    qdarktheme.setup_theme(theme, "rounded", custom_colors={"primary": "#ffd815"}) # Apply theme
    settings.setValue("appAppearanceMode",theme)


# ----------------------------
# Entrypoint
# ----------------------------
class MainWindow(QMainWindow, Mixin):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.app_icon: str = APP_ICON.as_posix()
        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        self.setWindowIcon(QIcon(self.app_icon))
        # Init directories
        self.root_dir = Path(__file__).parent
        self.config_dir: Path = self.root_dir / "config"
        self.log_pattern_config: Path = self.config_dir / "log_patterns.json"
        self.gui_settings_config: Path = self.config_dir / "gui_settings.json"
        # Application settings
        self.settings = QSettings("Jovan", "LobsterLogReporter")

        self.thread_pool: QThreadPool = QThreadPool()  # Thread pool

        self.initialize_ui_all()  # From Mixin class
        self.ui_state_manager.initial_ui_state_on_start()
        self.load_app_settings() # Load initial application's settings

    def load_app_settings(self) -> None:
        """Load application settings from QSettings."""
        # Restore geometry safely
        restore_window_state(self, self.settings)
        restore_splitter_state(self.ui.splitterTop, self.settings)
        # Initialize theme/style for application
        theme = self.settings.value("appAppearanceMode", str("dark"))
        initialize_theme(self, theme, self.settings)
        self.ui.statusbar.showMessage("Application settings loaded.", 5000)  # Shows message in statusbar

    # Helper method to save apps settings in a more DRY way
    def save_app_settings(self) -> None:
        """Save application settings to QSettings."""
        save_window_state(self, self.settings)  # Save windows location and state
        save_splitter_state(self.ui.splitterTop, self.settings)
        self.settings.sync()  # optional: force write to disk

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle application close event to save settings."""
        self.save_app_settings()
        event.accept()  # Accept the event to close the application


if __name__ == "__main__":
    qdarktheme.enable_hi_dpi()
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
