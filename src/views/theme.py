"""Design tokens, light/dark style sheet and tinted line icons for the Glint GUI.

The theme follows the operating system colour scheme and re-applies itself
live when the user switches between light and dark mode.
"""

from __future__ import annotations

import sys
import tempfile
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from PySide6.QtCore import QByteArray, QObject, QRectF, QSettings, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QGuiApplication, QIcon, QPainter, QPalette, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QApplication


# ================================================================== tokens


@dataclass(frozen=True, slots=True)
class Tokens:
    dark: bool
    window: str  # app background (content area)
    sidebar: str  # sidebar background
    surface: str  # cards, inputs
    surface_alt: str  # hover / alternate rows / segmented track
    border: str
    border_strong: str
    text: str
    text_muted: str
    text_faint: str
    accent: str
    accent_hover: str
    accent_pressed: str
    accent_text: str  # text drawn on top of the accent colour
    accent_soft: str  # tinted backgrounds (chips, selection)
    success: str
    success_soft: str
    warning: str
    warning_soft: str
    danger: str
    danger_soft: str
    log_bg: str


LIGHT = Tokens(
    dark=False,
    window="#f6f7f9",
    sidebar="#ffffff",
    surface="#ffffff",
    surface_alt="#f1f3f6",
    border="#e4e7ec",
    border_strong="#cfd4dc",
    text="#101828",
    text_muted="#475467",
    text_faint="#98a2b3",
    accent="#5b5bd6",
    accent_hover="#4f4fc4",
    accent_pressed="#4444ad",
    accent_text="#ffffff",
    accent_soft="#ededfc",
    success="#12805c",
    success_soft="#e3f5ee",
    warning="#b54708",
    warning_soft="#fdf0e1",
    danger="#d92d20",
    danger_soft="#fdecea",
    log_bg="#fbfbfc",
)

DARK = Tokens(
    dark=True,
    window="#111113",
    sidebar="#18181b",
    surface="#1c1c20",
    surface_alt="#26262b",
    border="#2c2c32",
    border_strong="#3a3a42",
    text="#ededef",
    text_muted="#a1a1aa",
    text_faint="#6b6b75",
    accent="#7c7cf0",
    accent_hover="#8e8ef3",
    accent_pressed="#6a6ae0",
    accent_text="#ffffff",
    accent_soft="#25254a",
    success="#3dd68c",
    success_soft="#123526",
    warning="#f5a524",
    warning_soft="#3a2a10",
    danger="#ff6369",
    danger_soft="#3b1618",
    log_bg="#141417",
)

RADIUS = 8
RADIUS_LG = 12


# =================================================================== icons

APP_ICON_PATH = Path(__file__).resolve().parents[2] / "assets" / "glint.ico"
APP_LOGO_PATH = Path(__file__).resolve().parents[2] / "assets" / "glint.png"


def app_icon() -> QIcon:
    """The Glint application icon (window, taskbar, dialogs)."""
    return QIcon(str(APP_ICON_PATH))


# 24x24 line icons, stroke-only so they can be tinted with ``currentColor``.
_ICON_PATHS: dict[str, str] = {
    "play": '<path d="M7 4.5v15l12-7.5z" fill="currentColor" stroke="none"/>',
    "stop": '<rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" stroke="none"/>',
    "folder": '<path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/>',
    "file": '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5"/>',
    "sheet": '<rect x="4" y="4" width="16" height="16" rx="2"/><path d="M4 10h16M4 15h16M10 4v16"/>',
    "refresh": '<path d="M20 11a8 8 0 0 0-14.6-4.5L4 8"/><path d="M4 4v4h4"/>'
    '<path d="M4 13a8 8 0 0 0 14.6 4.5L20 16"/><path d="M20 20v-4h-4"/>',
    "dots": '<circle cx="6" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="18" cy="12" r="1.2"/>',
    "table": '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M9 10v9"/>',
    "terminal": '<rect x="3" y="4" width="18" height="16" rx="2"/><path d="M7 9l3 3-3 3M13 15h4"/>',
    "search": '<circle cx="11" cy="11" r="6.5"/><path d="M20 20l-4.2-4.2"/>',
    "chevron-down": '<path d="M6 9l6 6 6-6"/>',
    "sparkle": '<path d="M12 3l1.9 5.6L19.5 10.5l-5.6 1.9L12 18l-1.9-5.6L4.5 10.5l5.6-1.9z" '
    'fill="currentColor" stroke="none"/><path d="M19 3v4M17 5h4" />',
    "sun": '<circle cx="12" cy="12" r="4"/><path d="M12 2.5v2M12 19.5v2M2.5 12h2M19.5 12h2'
    'M5.3 5.3l1.4 1.4M17.3 17.3l1.4 1.4M5.3 18.7l1.4-1.4M17.3 6.7l1.4-1.4"/>',
    "moon": '<path d="M20 14.5A8 8 0 0 1 9.5 4a8 8 0 1 0 10.5 10.5z"/>',
    "monitor": '<rect x="3" y="4" width="18" height="12" rx="2"/><path d="M8 20h8M12 16v4"/>',
    "inbox": '<path d="M3 13l3-8h12l3 8v5a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"/><path d="M3 13h5l1 3h6l1-3h5"/>',
    "edit": '<path d="M4 20h4L19 9a2.8 2.8 0 0 0-4-4L4 16z"/><path d="M13.5 6.5l4 4"/>',
    "plus": '<path d="M12 5v14M5 12h14"/>',
    "trash": '<path d="M4 7h16M10 11v6M14 11v6"/><path d="M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12"/>'
    '<path d="M9 7V4h6v3"/>',
    "arrow-up": '<path d="M12 19V5M6 11l6-6 6 6"/>',
    "arrow-down": '<path d="M12 5v14M6 13l6 6 6-6"/>',
    "undo": '<path d="M9 14L4 9l5-5"/><path d="M4 9h11a5 5 0 0 1 0 10h-3"/>',
    "save": '<path d="M5 3h11l4 4v12a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z"/>'
    '<path d="M8 3v5h7V3M8 21v-7h8v7"/>',
    "alert": '<circle cx="12" cy="12" r="9"/><path d="M12 7.5v5.5"/>'
    '<circle cx="12" cy="16.5" r="0.6" fill="currentColor"/>',
}


def _svg(name: str, color: str, stroke_width: float = 1.8) -> bytes:
    body = _ICON_PATHS[name].replace("currentColor", color)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
        f'stroke="{color}" stroke-width="{stroke_width}" stroke-linecap="round" '
        f'stroke-linejoin="round">{body}</svg>'
    ).encode()


def icon(name: str, color: str, size: int = 18) -> QIcon:
    """Render a tinted line icon (crisp on high-DPI screens)."""
    screen = QGuiApplication.primaryScreen()
    dpr = screen.devicePixelRatio() if screen else 1.0
    renderer = QSvgRenderer(QByteArray(_svg(name, color)))
    pixmap = QPixmap(QSize(round(size * dpr), round(size * dpr)))
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    renderer.render(painter, QRectF(0, 0, pixmap.width(), pixmap.height()))
    painter.end()
    pixmap.setDevicePixelRatio(dpr)
    return QIcon(pixmap)


def _icon_file(name: str, color: str) -> str:
    """Write an icon as a file so it can be referenced from the style sheet."""
    folder = Path(tempfile.gettempdir()) / "glint-theme"
    folder.mkdir(exist_ok=True)
    path = folder / f"{name}-{color.lstrip('#')}.svg"
    if not path.exists():
        path.write_bytes(_svg(name, color, 2.2))
    return path.as_posix()


# ============================================================ style sheet


def _style_sheet(t: Tokens) -> str:
    chevron = _icon_file("chevron-down", t.text_muted)
    return f"""
* {{ outline: none; }}
QMainWindow, QWidget#Content {{ background: {t.window}; }}
QWidget {{ color: {t.text}; }}
QToolTip {{
    background: {t.surface}; color: {t.text}; border: 1px solid {t.border_strong};
    border-radius: 6px; padding: 6px 8px;
}}

/* ---------- sidebar ---------- */
QFrame#Sidebar {{ background: {t.sidebar}; border-right: 1px solid {t.border}; }}
QFrame#Sidebar QScrollArea, QFrame#Sidebar QScrollArea > QWidget > QWidget {{ background: transparent; }}
QFrame#SidebarFooter {{ background: {t.sidebar}; border-top: 1px solid {t.border}; }}
QLabel#BrandTitle {{ font-size: 17px; font-weight: 650; }}
QLabel#BrandSubtitle {{ color: {t.text_muted}; font-size: 12px; }}
QToolButton#ThemeButton {{ background: transparent; border: 1px solid transparent; }}
QToolButton#ThemeButton:hover {{ background: {t.surface_alt}; border-color: {t.border}; }}
QLabel#SectionTitle {{
    color: {t.text_faint}; font-size: 11px; font-weight: 650; letter-spacing: 0.6px;
}}
QLabel#FieldLabel {{ color: {t.text_muted}; font-size: 12px; font-weight: 550; }}
QLabel#Hint {{ color: {t.text_faint}; font-size: 11.5px; }}
QLabel#Validation {{
    color: {t.danger}; background: {t.danger_soft}; border-radius: 6px; padding: 7px 10px;
    font-size: 12px;
}}
QLabel#Chip {{
    background: {t.accent_soft}; color: {t.accent}; border-radius: 10px;
    padding: 2px 9px; font-size: 11.5px; font-weight: 550;
}}
QLabel#ChipEmpty {{ color: {t.text_faint}; font-size: 12px; }}
QFrame#Divider {{ background: {t.border}; max-height: 1px; min-height: 1px; border: none; }}

/* ---------- inputs ---------- */
QLineEdit, QComboBox {{
    background: {t.surface}; border: 1px solid {t.border_strong}; border-radius: {RADIUS}px;
    padding: 0 10px; min-height: 32px; selection-background-color: {t.accent};
    selection-color: {t.accent_text};
}}
QLineEdit:hover, QComboBox:hover {{ border-color: {t.text_faint}; }}
QLineEdit:focus, QComboBox:focus, QComboBox:on {{ border: 1px solid {t.accent}; }}
QLineEdit:disabled, QComboBox:disabled {{ color: {t.text_faint}; background: {t.surface_alt}; border-color: {t.border}; }}
QComboBox::drop-down {{ border: none; width: 28px; subcontrol-origin: padding; subcontrol-position: center right; }}
QComboBox::down-arrow {{ image: url("{chevron}"); width: 14px; height: 14px; }}
QComboBox QAbstractItemView {{
    background: {t.surface}; border: 1px solid {t.border_strong}; border-radius: {RADIUS}px;
    padding: 4px; selection-background-color: {t.accent_soft}; selection-color: {t.text};
}}

/* ---------- buttons ---------- */
QPushButton, QToolButton {{
    background: {t.surface}; border: 1px solid {t.border_strong}; border-radius: {RADIUS}px;
    padding: 0 12px; min-height: 32px; font-weight: 550;
}}
QToolButton {{ padding: 0; min-width: 34px; max-width: 34px; min-height: 34px; max-height: 34px; }}
QPushButton:hover, QToolButton:hover {{ background: {t.surface_alt}; }}
QPushButton:pressed, QToolButton:pressed {{ background: {t.border}; }}
QPushButton:disabled, QToolButton:disabled {{ color: {t.text_faint}; border-color: {t.border}; background: transparent; }}

QPushButton#Primary {{
    background: {t.accent}; color: {t.accent_text}; border: none; min-height: 40px;
    font-size: 13.5px; font-weight: 600; border-radius: {RADIUS}px;
}}
QPushButton#Primary:hover {{ background: {t.accent_hover}; }}
QPushButton#Primary:pressed {{ background: {t.accent_pressed}; }}
QPushButton#Primary:disabled {{ background: {t.surface_alt}; color: {t.text_faint}; }}

QPushButton#Danger {{
    background: {t.danger_soft}; color: {t.danger}; border: 1px solid transparent; min-height: 40px;
    font-size: 13.5px; font-weight: 600;
}}
QPushButton#Danger:hover {{ border-color: {t.danger}; }}

QPushButton#Ghost {{ background: transparent; border: 1px solid transparent; color: {t.text_muted}; }}
QPushButton#Ghost:hover {{ background: {t.surface_alt}; color: {t.text}; }}
QPushButton#Ghost:disabled {{ color: {t.text_faint}; background: transparent; }}

/* ---------- segmented control ---------- */
QFrame#Segmented {{ background: {t.surface_alt}; border-radius: {RADIUS}px; }}
QFrame#Segmented QPushButton {{
    background: transparent; border: none; border-radius: 6px; min-height: 28px;
    padding: 0 14px; color: {t.text_muted};
}}
QFrame#Segmented QPushButton:hover {{ color: {t.text}; }}
QFrame#Segmented QPushButton:checked {{ background: {t.surface}; color: {t.text}; border: 1px solid {t.border}; }}

/* ---------- content ---------- */
QLabel#PageTitle {{ font-size: 22px; font-weight: 650; }}
QLabel#StatusText {{ color: {t.text_muted}; font-size: 12.5px; }}
QLabel#Pill {{ border-radius: 11px; padding: 3px 10px; font-size: 11.5px; font-weight: 650; }}
QLabel#Pill[tone="idle"] {{ background: {t.surface_alt}; color: {t.text_muted}; }}
QLabel#Pill[tone="running"] {{ background: {t.accent_soft}; color: {t.accent}; }}
QLabel#Pill[tone="success"] {{ background: {t.success_soft}; color: {t.success}; }}
QLabel#Pill[tone="warning"] {{ background: {t.warning_soft}; color: {t.warning}; }}
QLabel#Pill[tone="danger"] {{ background: {t.danger_soft}; color: {t.danger}; }}

QFrame#Card {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {RADIUS_LG}px; }}
QFrame#StatCard {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {RADIUS_LG}px; }}
QLabel#StatLabel {{ color: {t.text_muted}; font-size: 12px; font-weight: 550; }}
QLabel#StatValue {{ font-size: 22px; font-weight: 650; }}
QLabel#StatValueSmall {{ font-size: 13px; font-weight: 600; }}
QLabel#CardCaption {{ color: {t.text_faint}; font-size: 12px; }}
QLabel#EmptyTitle {{ font-size: 15px; font-weight: 600; }}
QLabel#EmptyText {{ color: {t.text_muted}; font-size: 12.5px; }}

QProgressBar {{ background: {t.surface_alt}; border: none; border-radius: 2px; max-height: 4px; min-height: 4px; }}
QProgressBar::chunk {{ background: {t.accent}; border-radius: 2px; }}

/* ---------- table ---------- */
QTableView {{
    background: {t.surface}; alternate-background-color: {t.surface_alt}; border: none;
    gridline-color: transparent; selection-background-color: {t.accent_soft};
    selection-color: {t.text}; font-size: 12.5px;
}}
QTableView::item {{ padding: 0 10px; border: none; }}
QHeaderView {{ background: {t.surface}; border: none; }}
QHeaderView::section {{
    background: {t.surface}; color: {t.text_muted}; border: none;
    border-bottom: 1px solid {t.border}; border-right: 1px solid {t.border};
    padding: 8px 10px; font-size: 12px; font-weight: 600;
}}
QHeaderView::section:vertical {{ color: {t.text_faint}; font-weight: 500; padding: 0 8px; border-right: 1px solid {t.border}; border-bottom: none; }}
QTableCornerButton::section {{ background: {t.surface}; border: none; border-bottom: 1px solid {t.border}; border-right: 1px solid {t.border}; }}

QPlainTextEdit#LogView {{
    background: {t.log_bg}; border: none; border-bottom-left-radius: {RADIUS_LG}px;
    border-bottom-right-radius: {RADIUS_LG}px; padding: 10px 12px; font-size: 12px;
    selection-background-color: {t.accent_soft}; selection-color: {t.text};
}}

/* ---------- pattern editor ---------- */
QDialog#PatternEditor {{ background: {t.window}; }}
QFrame#EditorPane {{ background: {t.surface}; border: 1px solid {t.border}; border-radius: {RADIUS_LG}px; }}
QFrame#DialogFooter {{ background: {t.sidebar}; border-top: 1px solid {t.border}; }}
QLabel#DialogTitle {{ font-size: 18px; font-weight: 650; }}
QLabel#DialogPath {{ color: {t.text_faint}; font-size: 12px; }}
QLabel#FieldError {{ color: {t.danger}; font-size: 11.5px; }}
QLabel#Summary {{ color: {t.text_muted}; font-size: 12px; }}
QLabel#Summary[tone="danger"] {{ color: {t.danger}; }}
QLabel#Summary[tone="warning"] {{ color: {t.warning}; }}
QListView#CategoryList, QTableView#PatternTable, QPlainTextEdit#RegexEdit {{
    background: {t.surface}; border: 1px solid {t.border_strong}; border-radius: {RADIUS}px;
    selection-background-color: {t.accent_soft}; selection-color: {t.text};
}}
QListView#CategoryList {{ padding: 4px; }}
QListView#CategoryList::item {{ padding: 6px 8px; border-radius: 6px; }}
QListView#CategoryList::item:hover {{ background: {t.surface_alt}; }}
QListView#CategoryList::item:selected {{ background: {t.accent_soft}; color: {t.text}; }}
QTableView#PatternTable {{ alternate-background-color: {t.surface_alt}; }}
QListView#CategoryList:focus, QTableView#PatternTable:focus, QPlainTextEdit#RegexEdit:focus {{
    border: 1px solid {t.accent};
}}
QPlainTextEdit#RegexEdit {{ padding: 6px 8px; }}
QPlainTextEdit#RegexEdit:disabled {{ background: {t.surface_alt}; border-color: {t.border}; }}
QLineEdit[invalid="true"], QPlainTextEdit#RegexEdit[invalid="true"] {{ border: 1px solid {t.danger}; }}

/* ---------- scroll bars ---------- */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle {{ background: {t.border_strong}; border-radius: 3px; }}
QScrollBar::handle:vertical {{ min-height: 32px; }}
QScrollBar::handle:horizontal {{ min-width: 32px; }}
QScrollBar::handle:hover {{ background: {t.text_faint}; }}
QScrollBar::add-line, QScrollBar::sub-line {{ width: 0; height: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}
"""


def _palette(t: Tokens) -> QPalette:
    """Palette for native parts (file dialogs, menus) that ignore the style sheet."""
    p = QPalette()
    role = QPalette.ColorRole
    p.setColor(role.Window, QColor(t.window))
    p.setColor(role.WindowText, QColor(t.text))
    p.setColor(role.Base, QColor(t.surface))
    p.setColor(role.AlternateBase, QColor(t.surface_alt))
    p.setColor(role.Text, QColor(t.text))
    p.setColor(role.Button, QColor(t.surface))
    p.setColor(role.ButtonText, QColor(t.text))
    p.setColor(role.Highlight, QColor(t.accent))
    p.setColor(role.HighlightedText, QColor(t.accent_text))
    p.setColor(role.ToolTipBase, QColor(t.surface))
    p.setColor(role.ToolTipText, QColor(t.text))
    p.setColor(role.PlaceholderText, QColor(t.text_faint))
    p.setColor(role.Mid, QColor(t.border_strong))
    p.setColor(role.Link, QColor(t.accent))
    for r in (role.Text, role.WindowText, role.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, r, QColor(t.text_faint))
    return p


def _ui_font() -> QFont:
    families = {
        "win32": ["Segoe UI Variable Text", "Segoe UI"],
        "darwin": [".AppleSystemUIFont", "Helvetica Neue"],
    }.get(sys.platform, ["Inter", "Cantarell", "Noto Sans"])
    font = QFont()
    font.setFamilies(families)
    font.setPointSizeF(9.75)
    font.setHintingPreference(QFont.HintingPreference.PreferNoHinting)
    return font


def mono_font() -> QFont:
    font = QFont()
    font.setFamilies(["Cascadia Mono", "JetBrains Mono", "Consolas", "Menlo", "monospace"])
    font.setStyleHint(QFont.StyleHint.Monospace)
    font.setPointSizeF(9.25)
    return font


# ================================================================ manager


class ThemeMode(str, Enum):
    SYSTEM = "system"
    LIGHT = "light"
    DARK = "dark"

    @property
    def label(self) -> str:
        return self.value.capitalize()

    def next(self) -> "ThemeMode":
        order = list(ThemeMode)
        return order[(order.index(self) + 1) % len(order)]


class ThemeManager(QObject):
    """Applies the theme to the application.

    In ``SYSTEM`` mode it follows the OS colour scheme live; ``LIGHT``/``DARK``
    force a scheme. The chosen mode is persisted in ``QSettings``.
    """

    changed = Signal(object)  # Tokens
    mode_changed = Signal(object)  # ThemeMode

    def __init__(self, app: QApplication, settings: QSettings | None = None) -> None:
        super().__init__(app)
        self._app = app
        self._settings = settings or QSettings("Glint", "Glint")
        self._tokens = LIGHT
        try:
            self._mode = ThemeMode(self._settings.value("theme_mode", ThemeMode.SYSTEM.value))
        except ValueError:
            self._mode = ThemeMode.SYSTEM
        app.setStyle("Fusion")
        app.setFont(_ui_font())
        app.styleHints().colorSchemeChanged.connect(self._on_system_scheme_changed)
        self.apply()

    @property
    def tokens(self) -> Tokens:
        return self._tokens

    @property
    def mode(self) -> ThemeMode:
        return self._mode

    def set_mode(self, mode: ThemeMode) -> None:
        if mode == self._mode:
            return
        self._mode = mode
        self._settings.setValue("theme_mode", mode.value)
        self.mode_changed.emit(mode)
        self.apply()

    def cycle_mode(self) -> None:
        self.set_mode(self._mode.next())

    def _on_system_scheme_changed(self, _: object) -> None:
        if self._mode is ThemeMode.SYSTEM:
            self.apply()

    def apply(self) -> None:
        if self._mode is ThemeMode.SYSTEM:
            dark = self._app.styleHints().colorScheme() == Qt.ColorScheme.Dark
        else:
            dark = self._mode is ThemeMode.DARK
        tokens = DARK if dark else LIGHT
        if tokens is self._tokens and self._app.styleSheet():
            return
        self._tokens = tokens
        self._app.setPalette(_palette(tokens))
        self._app.setStyleSheet(_style_sheet(tokens))
        self.changed.emit(tokens)
