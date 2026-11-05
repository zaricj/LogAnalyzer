"""Entry point for the Glint PySide6 desktop application.

Run from the project root:  uv run main_gui.py
"""

import logging
import sys

from PySide6.QtWidgets import QApplication

from src.viewmodels import MainViewModel
from src.views import MainWindow


def main() -> int:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    app = QApplication(sys.argv)
    app.setApplicationName("Glint")
    app.setOrganizationName("Glint")
    app.setStyle("Fusion")

    viewmodel = MainViewModel()
    window = MainWindow(viewmodel)
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
