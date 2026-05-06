from rich.console import Console
from rich.panel import Panel
from rich import print
from pathlib import Path

CONSOLE = Console()
RPRINT = print

def display_start_msg(
    patterns_config: Path,
    pattern_key: str,
    files_directory: Path,
    file_pattern: str,
    event_keyword: str,
):
    if not event_keyword:
        content = f"[bold blue]Pattern config: [/bold blue]{patterns_config}\n[bold blue]Pattern key: [/bold blue]{pattern_key}\n[bold blue]Searching dir: [/bold blue]{files_directory}\n[bold blue]File pattern: [/bold blue]{file_pattern}"
    else:
        content = f"[bold blue]Pattern config: [/bold blue]{patterns_config}\n[bold blue]Pattern key: [/bold blue]{pattern_key}\n[bold blue]Searching dir: [/bold blue]{files_directory}\n[bold blue]File pattern: [/bold blue]{file_pattern}\n[bold blue]Event keyword: [/bold blue]{event_keyword}"
    panel = Panel(
        content, title="[bold blue]Starting pipeline task[/bold blue]", expand=False
    )
    CONSOLE.print(panel)


def display_finished_msg(
    output_csv: str, excel_filename: str, total_time: str, rows_found: bool
):
    """Display completion message with consistent styling."""

    if rows_found:
        content = f"[green]CSV saved: {output_csv}\nExcel saved: {excel_filename}\n>>> ✓ Task has finished in {total_time} seconds. <<<[/green]"
        title = "[bold green]Success[/bold green]"
    else:
        content = f"[yellow]No matches were found, nothing to write.\n✓ Task has finished in {total_time} seconds.[/yellow]"
        title = "[bold yellow]Warning[/bold yellow]"

    panel = Panel(content, title=title, expand=False)
    CONSOLE.print(panel)
