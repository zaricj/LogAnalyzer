from collections.abc import Callable
from datetime import datetime, timezone
from pathlib import Path

from rich import print as rprint

# LOG_TIMESTAMP = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def display_start_msg(
    patterns_config: Path, pattern_key: str, files_directory: Path, file_pattern: str
):

    content = f"[bold blue]> Pattern config: [/bold blue]{patterns_config}\n[bold blue]> Pattern key: [/bold blue]{pattern_key}\n[bold blue]> Searching dir: [/bold blue]{files_directory}\n[bold blue]> File pattern: [/bold blue]{file_pattern}\n"
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
            # Apply the tag to the whole block clearly, or line by line
            content = (
                f"[green]CSV saved: {output_csv}[/green]\n"
                f"[green]Excel saved: {excel_filename}[/green]\n"
                f"[green]>>> ✓ Task has finished in {total_time} seconds. <<<[/green]"
            )
        else:
            content = (
                f"[green]CSV saved: {output_csv}[/green]\n"
                f"[green]>>> ✓ Task has finished in {total_time} seconds. <<<[/green]"
            )
    else:
        content = ("[yellow]\nNo matches were found, nothing to write.[/yellow]\n"
                    f"[yellow]✓ Task has finished in {total_time} seconds.[/yellow]")
    return content


def log(message: str, level: str = "info") -> None:
    """Log a message with timestamp and level."""
    timestamp = datetime.now(timezone.utc).strftime("%H:%M:%S")
    print(f"[{timestamp}] [{level.upper()}] {message}")


def announce(message: str, log_callback: Callable[[str], None] | None = None) -> None:
    """Announce a message using the provided callback or default rprint."""
    if log_callback:
        log_callback(message)
    else:
        rprint(message)


def format_error(error: Exception) -> str:
    """Format an exception into a readable error message."""
    return f"[bold red]Error:[/bold red] {type(error).__name__}: {error!s}"