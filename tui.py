from pathlib import Path
from numpy import place
from textual.app import App, ComposeResult
from textual.widgets import (
    Footer, Header, Label, Select, Button, 
    Input, Rule, Markdown, Collapsible, Static, Checkbox
)
from textual.containers import HorizontalGroup, VerticalScroll, VerticalGroup

from src.modules.core.utils import get_pattern_keys


PATTERNS_CONFIG = "src/patterns/patterns.json"

class WelcomeMessage(Static):
    """A self-contained welcome widget with collapsible markdown."""
    
    WELCOME_TEXT = """\
# Welcome to Glint ✨!

A powerful file analysis and pattern extraction tool designed to search through log files.

Extract structured information using regex patterns, and generate comprehensive reports.
"""

    def compose(self) -> ComposeResult:
        # We wrap the Markdown inside the Collapsible right here
        with Collapsible(title="Help & Information", collapsed=False):
            yield Markdown(self.WELCOME_TEXT)


class ComboboxPattern(HorizontalGroup):
    def compose(self) -> ComposeResult:
        # Load options here or in on_mount to avoid import-time I/O issues
        options = get_pattern_keys(Path(PATTERNS_CONFIG))
        yield Label("Pattern configuration:", id="label_select_pattern")
        yield Select(((opt, opt) for opt in options), id="select_pattern")


class SelectedFolder(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label("Search directory:     ", id="label_search_directory")
        yield Input(placeholder="Select a folder to search in...")
        yield Button(label="Browse", id="Btn_browse_folder", variant="default")


class FilePattern(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label("File filter pattern:  ", id="label_file_pattern")
        yield Input(placeholder="Set a file pattern (defaults to '*.log')")


class CSVFileName(HorizontalGroup):
    def compose(self):
        yield Label(content="CSV output filename:      ")
        yield Input(placeholder="Enter a filename for the output CSV file...")


class StartTask(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label(content="Run search task:      ")
        yield Button(label="Start Analysis", id="Btn_start_task", variant="success")
        yield Checkbox(label="Convert CSV file to Excel after task end?", value=False)


class PatternConfigurationArea(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield ComboboxPattern()
        yield SelectedFolder()
        yield FilePattern()


class ConfigurationArea(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield PatternConfigurationArea()
        yield Rule()
        yield CSVFileName()
        yield StartTask()


class GlintApp(App):
    CSS_PATH = "src/style/main.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "about", "About"),
    ]

    def compose(self) -> ComposeResult:
        yield Header()
        yield WelcomeMessage() # Now clean and self-contained
        yield Rule(line_style="heavy")
        with VerticalScroll():
            yield ConfigurationArea()
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.theme = "textual-dark" if self.theme == "textual-light" else "textual-light"

if __name__ == "__main__":
    GlintApp().run()