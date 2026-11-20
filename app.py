"""Entry point for the Glint PySide6 desktop application.

Run from the project root:  uv run app.py
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from src.viewmodels import MainViewModel
from src.views import MainWindow
from src.views.theme import ThemeManager, app_icon


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    if sys.platform == "win32":
        # Own taskbar identity, so Windows shows the Glint icon instead of python.exe's.
        import ctypes

        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Glint.LogAnalyzer")

    app = QApplication(sys.argv)
    app.setApplicationName("Glint")
    app.setOrganizationName("Glint")
    app.setWindowIcon(app_icon())
    theme = ThemeManager(app)

    viewmodel = MainViewModel()
    window = MainWindow(viewmodel, theme)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
