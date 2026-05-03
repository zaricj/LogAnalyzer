from pathlib import Path
from datetime import datetime
from tkinter import Tk, filedialog
import psutil
import os
from textual import work
import textual
from textual.app import App, ComposeResult
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
from textual.reactive import reactive
from textual.containers import Horizontal, HorizontalGroup, VerticalScroll, VerticalGroup
from textual.widgets._select import InvalidSelectValueError
from rich.table import Table
from rich.progress_bar import ProgressBar
from rich.text import Text

from src.modules.core.utils import get_pattern_keys
from src.modules.core.pipeline import execute_pipeline
from src.modules.io.settings_config import APP_SETTINGS_FILE, load_app_settings, get_all_setting_keys, get_setting_values

# Configuration constants
PATTERNS_CONFIG = "src/patterns/patterns.json"
# CSV output
OUTPUT_DIR = "output"
TIMESTAMP_PREFIX = datetime.now().strftime("%Y_%m_%d")

class WelcomeMessage(Static):
    """A self-contained welcome widget with collapsible markdown."""

    WELCOME_TEXT = """\
# Welcome to Glint ✨!

A powerful file analysis and pattern extraction tool designed to search through log files.
Extract structured information using regex patterns, and generate comprehensive reports.

## What It Does

Glint helps you:

- **Search and parse** various types of log files (application logs, SQL, FTP, HTTP, etc.)
- **Extract specific patterns** from log entries using regex-based definitions
- **Structure and organize** unstructured log data into actionable reports
- **Export results** to CSV for further analysis in spreadsheets
- **Process multiple files** concurrently with parallel threading
"""

    def compose(self) -> ComposeResult:
        # We wrap the Markdown inside the Collapsible right here
        with Collapsible(title="Help & Information", collapsed=False):
            yield Markdown(self.WELCOME_TEXT)


class StatPanel(Static):
    """A single stat display panel with a label, bar, and value."""

    value = reactive(0.0)

    BAR_WIDTH = 20
    FILLED = "█"
    EMPTY = "░"

    def __init__(self, label: str, unit: str = "%", max_val: float = 100.0, **kwargs):
        super().__init__(**kwargs)
        self.label = label
        self.unit = unit
        self.max_val = max_val

    def get_bar_style(self, pct: float) -> str:
        if pct > 80:
            return "bold red"
        elif pct > 50:
            return "bold yellow"
        return "bold green"

    def render(self) -> Text:
        pct = min((self.value / self.max_val) * 100, 100)
        filled = int((pct / 100) * self.BAR_WIDTH)
        empty = self.BAR_WIDTH - filled

        bar_style = self.get_bar_style(pct)

        text = Text()
        text.append(f" {self.label}\n", style="bold white")
        text.append(self.FILLED * filled, style=bar_style)
        text.append(self.EMPTY * empty, style="dim white")

        if self.unit == "MB":
            text.append(f"  {self.value:.1f} {self.unit}", style=bar_style)
        else:
            text.append(f"  {self.value:.0f}{self.unit}", style=bar_style)

        return text


class SystemStats(Static):
    """Displays live CPU, RAM, and App RAM stats in a horizontal panel."""

    cpu = reactive(0.0)
    ram = reactive(0.0)
    app_ram = reactive(0.0)

    def on_mount(self) -> None:
        self.process = psutil.Process(os.getpid())
        self.set_interval(1.0, self.update_stats)

    def update_stats(self) -> None:
        self.cpu = psutil.cpu_percent()
        self.ram = psutil.virtual_memory().percent
        self.app_ram = self.process.memory_info().rss / (1024 * 1024)

        self.query_one("#stat_cpu", StatPanel).value = self.cpu
        self.query_one("#stat_ram", StatPanel).value = self.ram
        self.query_one("#stat_app_ram", StatPanel).value = self.app_ram

    def compose(self) -> ComposeResult:
        yield Static("[bold underline]SYSTEM MONITOR[/bold underline]", id="stats_header")
        with Horizontal(id="stats_row"):
            yield StatPanel("CPU", unit="%", id="stat_cpu")
            yield Static("│", id="stats_divider_1", classes="stats_divider")
            yield StatPanel("RAM", unit="%", id="stat_ram")
            yield Static("│", id="stats_divider_2", classes="stats_divider")
            yield StatPanel("APP", unit="MB", max_val=500.0, id="stat_app_ram")

# ===== Horizontal widgets which are displayed in Vertical Group widgets ===== 

class LoadTask(HorizontalGroup):
    
    def get_saved_tasks(self) -> list[str]:
        data = load_app_settings(APP_SETTINGS_FILE)
        return get_all_setting_keys(data, "SavedTasksSetting")
    
    def compose(self):
        yield Label(content="Load saved task:")
        saved_tasks = self.get_saved_tasks()
        yield Select(
            ((task, task) for task in saved_tasks), prompt="Select a saved task to load...", id="select_task_to_load")
        yield Button("Load Task", id="button_load_task", variant="primary")


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
        yield Input(placeholder="Select a folder in which to perform the search...", id="input_directory")
        yield Button(label="Browse", id="button_browse_folder", variant="primary")


class FilePattern(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label("File pattern:", id="label_file_pattern")
        yield Input(
            placeholder="Specify a file pattern (defaults to *.log)",
            id="input_file_pattern",
        )


class CSVFileName(HorizontalGroup):
    def compose(self):
        yield Label(content="Output filename:")
        yield Input(
            placeholder="Specify a output filename, '.csv' will be appended automatically...",
            id="input_csv_filename",
        )


class StartTask(HorizontalGroup):
    def compose(self) -> ComposeResult:
        yield Label(content="Run search task:")
        yield Button(label="Start Task", id="button_start_task", variant="primary")
        yield Button(label="Save Task", id="button_save_task", variant="success")
        yield Checkbox(
            label="Convert CSV file to Excel after task end?",
            id="Chk_excel_conversion",
            value=False,
        )

# ===== END Horizontal widgets END ===== 

# ===== Vertical widgets =====

class PatternConfigurationContainer(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield Label("[underline]Search Configuration:[/underline]")
        yield ComboboxPattern()
        yield SelectedFolder()
        yield FilePattern()
        yield CSVFileName()


class TaskRunContainer(VerticalGroup):
    def compose(self):
        yield Label("[underline]Run task:[/underline]")
        yield LoadTask()
        yield StartTask()


class AppOutputContainer(VerticalGroup):
    def compose(self):
        with Collapsible(title="[bold underline]App Output:[/bold underline]", collapsed=False):
            yield RichLog(highlight=True, markup=True, id="main_log")


class ConfigurationContainer(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield PatternConfigurationContainer()

# ===== END Vertical widgets END =====

# ===== Main app class =====

class GlintApp(App):
    CSS_PATH = "src/style/main.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("a", "about", "About"),
    ]
    
    app_settings = load_app_settings(APP_SETTINGS_FILE)
    
    def build_output_path(self, csv_name: str | None, pattern_key: str) -> Path:
        """Build the output CSV file path."""
        # Ensure that the inputted filename for the csv
        # ends with the correct suffix '.csv'
        if csv_name:
            csv_name = csv_name + ".csv" if not csv_name.endswith(".csv") else csv_name
            return Path(f"{OUTPUT_DIR}/{csv_name}")
        else:
            return Path(f"{OUTPUT_DIR}/{TIMESTAMP_PREFIX}_{pattern_key}.csv")
    
    def gather_ui_values(self) -> dict:
        """Gather all UI input values into a configuration dict."""
        return {
            "pattern_key": self.query_one("#select_pattern", Select).value,
            "search_dir": self.query_one("#input_directory", Input).value,
            "file_filter": self.query_one("#input_file_pattern", Input).value,
            "csv_name": self.query_one("#input_csv_filename", Input).value,
            "excel_conversion": self.query_one("#Chk_excel_conversion", Checkbox).value,
        }

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the Start Task button press."""
        
        if event.button.id == "button_browse_folder":
        # Using tkinter for a native folder dialog
            root = Tk()
            root.withdraw() # Hides the small tk window
            folder_path = filedialog.askdirectory()
            root.destroy()
            
            if folder_path:
                self.query_one("#input_directory", Input).value = folder_path
                del root
                
        if event.button.id == "button_load_task":
            self.load_task_configuration()
                
        if event.button.id == "button_start_task":
            self.run_search_task()
            
    def load_task_configuration(self) -> None:
        """Loads the selected task via the button press"""
        log = self.query_one(RichLog)
        task_to_load = self.query_one("#select_task_to_load", Select).value
        task_settings = f"SavedTasksSetting.{task_to_load}"
        saved_task_values = get_setting_values(self.app_settings, task_settings, {})

        if saved_task_values:
            select_pattern = self.query_one("#select_pattern", Select)

            saved_pattern = saved_task_values.get("PatternConfiguration")

            valid_values = {v for _, v in select_pattern._options}

            if saved_pattern in valid_values:
                select_pattern.value = saved_pattern
            else:
                log.write(f"[bold yellow]WARNING:[/bold yellow] Skipping invalid pattern: [bold yellow]{saved_pattern}[/bold yellow]")

            self.query_one("#input_directory", Input).value = saved_task_values.get("SearchDirectory", "")
            self.query_one("#input_file_pattern", Input).value = saved_task_values.get("FilePattern", "")
            self.query_one("#input_csv_filename", Input).value = saved_task_values.get("OutputFilename", "")

    @work(thread=True)
    def run_search_task(self) -> None:
        """The background worker that runs your logic."""
        log = self.query_one(RichLog)  # Queries the RichLog widget
        btn = self.query_one("#button_start_task", Button)

        input_values = self.gather_ui_values()

        # Update UI State
        btn.disabled = True
        btn.label = "Searching..."
        log.display = True
        log.clear()
        log.write("[bold]Initializing Pipeline...\n[/bold]")

        try:

            execute_pipeline(
                patterns_config=Path(PATTERNS_CONFIG),
                pattern_key=input_values["pattern_key"],
                files_directory=Path(input_values["search_dir"]),
                file_pattern=input_values["file_filter"] or "*.log",
                output_csv= self.build_output_path(input_values["csv_name"], input_values["pattern_key"]),
                convert_to_excel = input_values["excel_conversion"],
                log_callback=log.write
            )

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {str(e)}")
        finally:
            btn.disabled = False
            btn.label = "Start Task"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="✨")
        yield SystemStats()
        yield Rule(line_style="heavy")
        with VerticalScroll():
            yield Rule()
            yield ConfigurationContainer()
            yield Rule()
            yield TaskRunContainer()
            yield Rule()
            yield AppOutputContainer()
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    GlintApp().run()
