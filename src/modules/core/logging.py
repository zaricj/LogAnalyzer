from rich import print as rprint
from datetime import datetime
from pathlib import Path
from typing import Callable

LOG_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def display_start_msg(
    patterns_config: Path, pattern_key: str, files_directory: Path, file_pattern: str
):

    content = f"[bold blue] > Pattern config: [/bold blue]{patterns_config}\n[bold blue] > Pattern key: [/bold blue]{pattern_key}\n[bold blue] > Searching dir: [/bold blue]{files_directory}\n[bold blue] > File pattern: [/bold blue]{file_pattern}\n"
    return content


def display_finished_msg(
    output_csv: str,
    excel_filename: str,
    total_time: str,
    rows_found: bool,
    convert_to_excel: bool,
):
    """Display completion message with consistent styling."""

    if rows_found:
        if convert_to_excel:
            content = f"[green]CSV saved: {output_csv}\nExcel saved: {excel_filename}\n>>> ✓ Task has finished in {total_time} seconds. <<<[/green]"
        else:
            content = f"[green]CSV saved: {output_csv}\n>>> ✓ Task has finished in {total_time} seconds. <<<[/green]"
    else:
        content = f"[yellow]No matches were found, nothing to write.\n✓ Task has finished in {total_time} seconds.[/yellow]"
    return content


def log(message: str, level: str = "info") -> None:
    """Log a message with timestamp and level."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level.upper()}] {message}")


def announce(message: str, log_callback: Callable[[str], None] = None) -> None:
    """Announce a message using the provided callback or default rprint."""
    if log_callback:
        log_callback(message)
    else:
        rprint(message)


def format_error(error: Exception) -> str:
    """Format an exception into a readable error message."""
    return f"[bold red]Error:[/bold red] {type(error).__name__}: {str(error)}"