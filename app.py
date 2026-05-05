from pathlib import Path
from datetime import datetime
from tkinter import Tk, filedialog
import psutil
import os
from textual import work
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
    TabbedContent,
    TabPane,
)
from textual.reactive import reactive
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    VerticalScroll,
    VerticalGroup,
)
from rich.text import Text

from src.modules.core.utils import get_pattern_keys
from src.modules.core.pipeline import execute_pipeline
from src.modules.io.settings_config import (
    APP_SETTINGS_FILE,
    load_app_settings,
    get_all_setting_keys,
    get_setting_values,
    set_setting_values,
)

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

    BAR_WIDTH = 25
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
        text.append(f"{self.label}\n", style="bold")
        text.append(self.FILLED * filled, style=bar_style)
        text.append(self.EMPTY * empty, style="dim")

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
    ram_mb_total = reactive(0.0)
    ram_mb_used = reactive(0.0)

    def on_mount(self) -> None:
        self.process = psutil.Process(os.getpid())
        self.set_interval(1.0, self.update_stats)

    def update_stats(self) -> None:
        virtual_mem = psutil.virtual_memory()
        self.cpu = psutil.cpu_percent()
        self.ram = virtual_mem.percent
        self.ram_mb_total = virtual_mem.total / (1024**2)
        self.ram_mb_used = virtual_mem.used / (1024**2)
        self.app_ram = self.process.memory_info().rss / (1024 * 1024)

        self.query_one("#stat_cpu", StatPanel).value = self.cpu
        self.query_one("#stat_ram", StatPanel).value = self.ram
        self.query_one("#stat_ram", StatPanel).label = f"RAM USAGE {self.ram_mb_used:.0f}/{self.ram_mb_total:.0f} MB"
        self.query_one("#stat_app_ram", StatPanel).value = self.app_ram

    def compose(self) -> ComposeResult:
        yield Static(
            "SYSTEM MONITOR", id="stats_header"
        )
        with Horizontal(id="stats_row"):
            yield StatPanel("CPU USAGE", unit="%", id="stat_cpu")
            yield Static("│", id="stats_divider_1", classes="stats_divider")
            yield StatPanel("RAM USAGE", unit="%", id="stat_ram")
            yield Static("│", id="stats_divider_2", classes="stats_divider")
            yield StatPanel("APP RAM USAGE", unit="MB", max_val=500.0, id="stat_app_ram")


# ===== Horizontal widgets which are displayed in Vertical Group widgets =====

class LoadTask(HorizontalGroup):
    def get_saved_tasks(self) -> list[str]:
        data = load_app_settings(APP_SETTINGS_FILE)
        return get_all_setting_keys(data, "SavedTasksSetting")

    def compose(self):
        yield Label(content="Load saved task:")
        saved_tasks = self.get_saved_tasks()
        yield Select(
            ((task, task) for task in saved_tasks),
            prompt="Select a saved task to load...",
            id="select_task_to_load",
        )
        yield Button("Load Task", id="button_load_task", variant="primary")


class SaveTask(HorizontalGroup):
    def compose(self):
        yield Label(content="Save task:")
        yield Input(placeholder="Enter a task name...", id="input_save_task_name")
        yield Button("Save Task", id="button_save_task", variant="success")


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
        yield Input(
            placeholder="Select a folder in which to perform the search...",
            id="input_directory",
        )
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
        yield SaveTask()
        yield StartTask()


class AppOutputContainer(VerticalGroup):
    def compose(self):
        with Collapsible(
            title="[bold underline]App Output:[/bold underline]", collapsed=False
        ):
            yield RichLog(highlight=True, markup=True, id="main_log")


class ConfigurationContainer(VerticalGroup):
    def compose(self) -> ComposeResult:
        yield PatternConfigurationContainer()


# ===== END Vertical widgets END =====

# ===== Main app class =====

class GlintApp(App):
    CSS_PATH = "src/style/main.tcss"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle Theme")
    ]

    def on_mount(self) -> None:
        # Load settings at runtime
        self.theme = "atom-one-dark"
        self.app_settings = load_app_settings(APP_SETTINGS_FILE)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _build_output_path(self, csv_name: str | None, pattern_key: str) -> Path:
        if csv_name:
            csv_name = csv_name if csv_name.endswith(".csv") else csv_name + ".csv"
            return Path(f"{OUTPUT_DIR}/{csv_name}")
        return Path(f"{OUTPUT_DIR}/{TIMESTAMP_PREFIX}_{pattern_key}.csv")

    def _gather_ui_values(self) -> dict:
        return {
            "pattern_key":      self.query_one("#select_pattern",      Select).value,
            "search_dir":       self.query_one("#input_directory",      Input).value,
            "file_filter":      self.query_one("#input_file_pattern",   Input).value,
            "csv_name":         self.query_one("#input_csv_filename",   Input).value,
            "excel_conversion": self.query_one("#Chk_excel_conversion", Checkbox).value,
        }

    def _log(self, msg: str) -> None:
        self.query_one(RichLog).write(msg)

    # ------------------------------------------------------------------
    # Button routing  (one handler, clean dispatch)
    # ------------------------------------------------------------------

    def on_button_pressed(self, event: Button.Pressed) -> None:
        dispatch = {
            "button_browse_folder": self._browse_folder,
            "button_load_task":     self._load_task,
            "button_save_task":     self._save_task,
            "button_start_task":    self._start_task,
        }
        handler = dispatch.get(event.button.id)
        if handler:
            handler()

    # ------------------------------------------------------------------
    # Button handlers
    # ------------------------------------------------------------------

    def _browse_folder(self) -> None:
        root = Tk()
        root.withdraw()
        folder = filedialog.askdirectory()
        root.destroy()
        if folder:
            self.query_one("#input_directory", Input).value = folder

    def _load_task(self) -> None:
        task_name = self.query_one("#select_task_to_load", Select).value
        key       = f"SavedTasksSetting.{task_name}"
        values    = get_setting_values(self.app_settings, key, {})

        if not values:
            self._log("[bold red]Error:[/bold red] No data found for that task.")
            return

        select = self.query_one("#select_pattern", Select)
        saved_pattern = values.get("PatternConfiguration")
        valid = {v for _, v in select._options}  
        
        if saved_pattern in valid:
            select.value = saved_pattern
        else:
            self._log(
                f"[bold yellow]WARNING:[/bold yellow] "
                f"Pattern [yellow]{saved_pattern}[/yellow] not found — skipped."
            )

        self.query_one("#input_directory",   Input).value = values.get("SearchDirectory", "")
        self.query_one("#input_file_pattern",Input).value = values.get("FilePattern",     "")
        self.query_one("#input_csv_filename",Input).value = values.get("OutputFilename",  "")
        self._log(f"Task [bold green]'{task_name}'[/bold green] loaded.")

    def _save_task(self) -> None:
        name = self.query_one("#input_save_task_name", Input).value.strip()
        if not name:
            self._log("[bold red]Error:[/bold red] Please enter a task name.")
            return

        values = self._gather_ui_values()
        key    = f"SavedTasksSetting.{name.replace(' ', '_')}"
        data   = {
            "PatternConfiguration": values["pattern_key"],
            "SearchDirectory":      values["search_dir"],
            "FilePattern":          values["file_filter"],
            "OutputFilename":       values["csv_name"],
        }
        set_setting_values(self.app_settings, key, data)

        # Refresh load-task dropdown
        updated = get_all_setting_keys(self.app_settings, "SavedTasksSetting")
        self.query_one("#select_task_to_load", Select).set_options(
            [(t, t) for t in updated]
        )
        self._log(f"[bold green]Saved:[/bold green] task '{name}'.")

    def _start_task(self) -> None:
        self._run_search_task()

    @work(thread=True)
    def _run_search_task(self) -> None:
        """The background worker that runs your logic."""
        log = self.query_one(RichLog)  # Queries the RichLog widget
        btn = self.query_one("#button_start_task", Button)

        input_values = self._gather_ui_values()

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
                output_csv=self._build_output_path(input_values["csv_name"], input_values["pattern_key"]),
                convert_to_excel=input_values["excel_conversion"],
                log_callback=log.write,
            )

        except Exception as e:
            log.write(f"[bold red]Error:[/bold red] {str(e)}")
        finally:
            btn.disabled = False
            btn.label = "Start Task"

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True, icon="✨")
        yield SystemStats()
        
        with TabbedContent(initial="tab_config"):
            with TabPane("Help & Info", id="tab_help"):
                yield WelcomeMessage()
            
            with TabPane("Configuration", id="tab_config"):
                with VerticalScroll():
                    yield ConfigurationContainer()
                    yield Rule()
                    yield TaskRunContainer()
                    yield RichLog(highlight=True, markup=True, id="main_log")
                    
        yield Footer()

    def action_toggle_dark(self) -> None:
        self.theme = (
            "atom-one-dark" if self.theme == "atom-one-light" else "atom-one-light"
        )


if __name__ == "__main__":
    GlintApp().run()
