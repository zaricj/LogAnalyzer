from pathlib import Path
import time
import itertools
from rich.panel import Panel


from src.modules.core.ui import CONSOLE, rprint
from src.modules.core.parser import collect_rows
from src.modules.io.config import load_pattern_search_rule
from src.modules.io.file_utils import get_files_in_folder
from src.modules.io.exporters import write_csv, convert_csv_to_excel


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


# ========== Pipeline ==========


def work(files, separator_regex, compiled, output_csv, event_keyword, show_progress):
    start = time.time()  # Process start time
    excel_filename = ""
    # Collect rows as generator object
    row_generator = collect_rows(
        files, separator_regex, compiled, event_keyword, show_progress
    )
    first_row = next(row_generator, None)

    if first_row is None:
        end = time.time()
        total_time = f"{end - start:.2f}"
        display_finished_msg("", "", total_time, False)
        return

    # Collect headers from the extracted first row
    headers = ["timestamp"] + [
        h for h in first_row.keys() if h not in ("time", "timestamp")
    ]
    # Stitch the first row back together with the remaining generator
    full_generator = itertools.chain([first_row], row_generator)

    # Pass the stitched generator to the writer
    count = write_csv(output_csv, headers, full_generator)
    rprint(
        f"[bold green]✓ Writing to csv has finished, wrote [bold yellow]{count}[/bold yellow] rows...[/bold green]"
    )

    if count <= 1_048_576:
        excel_filename = output_csv.with_suffix(".xlsx")
        convert_csv_to_excel(output_csv, excel_filename)  # Convert to excel
        rprint("[bold green]✓ CSV converted to excel format.[/bold green]")
    else:
        rprint(
            "[bold yellow]✖ CSV exceeds Excel's 1,048,576 row limit; Conversion to Excel is not possible."
        )
        excel_filename = ""

    end = time.time()
    total_time = f"{end - start:.2f}"
    display_finished_msg(str(output_csv), str(excel_filename), total_time, True)


def run_pipeline(
    patterns_config: Path,
    pattern_key: str,
    files_directory: Path,
    file_pattern: str,
    output_csv: Path,
    event_keyword: str = "",
    show_progress: bool = False,
):

    display_start_msg(
        patterns_config, pattern_key, files_directory, file_pattern, event_keyword
    )

    files = get_files_in_folder(files_directory, file_pattern)

    if not files:
        raise ValueError(
            f"No files found in {files_directory}, using pattern {file_pattern}"
        )

    compiled, separator_regex = load_pattern_search_rule(patterns_config, pattern_key)

    rprint("[bold]>>> Searching files for matches and writing results to csv...[/bold]")
    
    work(files, separator_regex, compiled, output_csv, event_keyword, show_progress)
