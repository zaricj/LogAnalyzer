from multiprocessing import Value
from pathlib import Path
from textual import work
from textual.app import App, ComposeResult
from textual.types import NoSelection
from textual.widgets import (
    Footer,
    Header,
    Label,
    Select,
    Button,
    Input,
    Rule,
    Markdown,
    Collapsible,
    Static,
    Checkbox,
    RichLog,
)
from textual.containers import HorizontalGroup, VerticalScroll, VerticalGroup

from rich import print as rprint
from src.modules.core.utils import get_pattern_keys
from datetime import datetime

# Configuration constants
PATTERNS_CONFIG = "src/patterns/patterns.json"
# CSV output
OUTPUT_DIR = "output"
TIMESTAMP_PREFIX = datetime.now().strftime("%Y_%m_%d")

def announce(msg, log_callback):
    if log_callback:
        log_callback(msg)
    else:
        rprint(msg)


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
        yield Select(
            ((opt, opt) for opt in options),
            prompt="Select a pattern configuration...",
            id="select_pattern",
        )


class SelectedFolder(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label("Search directory:", id="label_search_directory")
        yield Input(placeholder="Select a folder to search in...", id="input_directory")
        yield Button(label="Browse", id="Btn_browse_folder", variant="primary")


class FilePattern(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label("File filter pattern:", id="label_file_pattern")
        yield Input(
            placeholder="Set a file pattern (defaults to *.log)",
            id="input_file_pattern",
        )


class CSVFileName(HorizontalGroup):
    def compose(self):
        yield Label(content="CSV output filename:")
        yield Input(
            placeholder="Enter a name for the CSV file, suffix '.csv' is added automatically...",
            id="input_csv_filename",
        )


class StartTask(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label(content="Run search task:")
        yield Button(label="Start Task", id="Btn_start_task", variant="primary")
        yield Checkbox(
            label="Convert CSV file to Excel after task end?",
            id="Chk_excel_conversion",
            value=False,
        )


class AppOutput(RichLog):
    pass


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
        yield Rule()
        yield AppOutput(highlight=True, markup=True, id="main_log")

# ===== Main app class =====

class GlintApp(App):
    CSS_PATH = "src/style/main.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "about", "About"),
    ]

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the Start Task button press."""
        if event.button.id == "Btn_start_task":
            self.run_search_task()

    @work(thread=True)
    def run_search_task(self) -> None:
        """The background worker that runs your logic."""
        log = self.query_one(RichLog)  # Queries the RichLog widget
        btn = self.query_one("#Btn_start_task", Button)

        # Gather UI values (with fixed IDs)
        pattern_key = self.query_one("#select_pattern", Select).value
        search_dir = self.query_one("#input_directory", Input).value
        file_filter = self.query_one("#input_file_pattern", Input).value
        csv_name = self.query_one("#input_csv_filename", Input).value
        excel_conversion = self.query_one("#Chk_excel_conversion", Checkbox).value

        # Ensure that the inputted filename for the csv
        # ends with the correct suffix '.csv'
        if csv_name != "" and not csv_name.endswith(".csv"):
            csv_name = csv_name + ".csv"

        # Update UI State
        btn.disabled = True
        btn.label = "Searching..."
        log.display = True
        log.clear()
        log.write("[bold]Initializing Pipeline...\n[/bold]")

        try:
            CSV_FILE = (
                Path(f"{OUTPUT_DIR}/{csv_name}")
                if csv_name != ""
                else Path(f"{OUTPUT_DIR}/{TIMESTAMP_PREFIX}_{pattern_key}.csv")
            )

            # Call the logic
            from src.modules.core.pipeline import run_pipeline

            run_pipeline(
                patterns_config=Path(PATTERNS_CONFIG),
                pattern_key=pattern_key,
                files_directory=Path(search_dir),
                file_pattern=file_filter or "*.log",
                output_csv=CSV_FILE,
                convert_to_excel = excel_conversion,
                log_callback=log.write
            )

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {str(e)}")
        finally:
            btn.disabled = False
            btn.label = "Start Task"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="✨")
        yield WelcomeMessage()
        yield Rule(line_style="heavy")
        with VerticalScroll():
            yield ConfigurationArea()
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    GlintApp().run()
