from pathlib import Path
from re import Pattern
import time
import itertools
from app import announce
from src.modules.core.parser import collect_rows
from src.modules.io.config import load_pattern_search_rule
from src.modules.io.file_utils import get_files_in_folder
from src.modules.io.exporters import write_csv, convert_csv_to_excel


def display_start_msg(
    patterns_config: Path, pattern_key: str, files_directory: Path, file_pattern: str
):

    content = f"[bold blue] > Pattern config: [/bold blue]{patterns_config}\n[bold blue] > Pattern key: [/bold blue]{pattern_key}\n[bold blue] > Searching dir: [/bold blue]{files_directory}\n[bold blue] > File pattern: [/bold blue]{file_pattern}\n"
    return content


def display_finished_msg(
    output_csv: str, excel_filename: str, total_time: str, rows_found: bool, convert_to_excel: bool
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


# ========== Pipeline ==========


def work(
    files: list[str],
    separator_regex: Pattern,
    compiled: Pattern,
    output_csv: Path,
    convert_to_excel: bool,
    log_callback: callable,
):
    start = time.time()  # Process start time
    excel_filename = ""

    # Collect rows as generator object
    row_generator = collect_rows(files, separator_regex, compiled, log_callback)
    first_row = next(row_generator, None)

    if first_row is None:
        end = time.time()
        total_time = f"{end - start:.2f}"
        content = display_finished_msg("", "", total_time, False, convert_to_excel)
        announce(content, log_callback)
        return

    # Collect headers from the extracted first row
    headers = ["timestamp"] + [
        h for h in first_row.keys() if h not in ("time", "timestamp")
    ]
    # Stitch the first row back together with the remaining generator
    full_generator = itertools.chain([first_row], row_generator)

    # Pass the stitched generator to the writer
    count = write_csv(output_csv, headers, full_generator)

    announce(f"[bold green]✓ Writing to csv has finished, wrote [bold yellow]{count}[/bold yellow] rows...[/bold green]", log_callback)

    if convert_to_excel:  # Flag if conversion to excel should be done
        if count <= 1_048_576:
            excel_filename = output_csv.with_suffix(".xlsx")
            convert_csv_to_excel(output_csv, excel_filename, log_callback)  # Convert to excel
            announce("[bold green]✓ CSV converted to excel format.[/bold green]", log_callback)
        else:
            announce("[bold yellow]✖ CSV exceeds Excel's 1,048,576 row limit; Conversion to Excel is not possible.", log_callback)
            excel_filename = ""

    end = time.time()
    total_time = f"{end - start:.2f}"
    content = display_finished_msg(str(output_csv), str(excel_filename), total_time, True, convert_to_excel)
    announce(content, log_callback)


def validate_ui_inputs(files_directory: Path) -> None:
    if str(files_directory).strip() == ".":
        raise ValueError("Directory path to search not provided.")


def run_pipeline(
    patterns_config: Path,
    pattern_key: str,
    files_directory: Path,
    file_pattern: str,
    output_csv: Path,
    convert_to_excel: bool,
    log_callback: callable = None,
) -> None:

    validate_ui_inputs(files_directory)
    files = get_files_in_folder(files_directory, file_pattern)
    if not files:
        raise ValueError(
            f"No files found in {files_directory} using file pattern {file_pattern}"
        )

    content = display_start_msg(
        patterns_config,
        pattern_key,
        files_directory,
        file_pattern,
    )
    announce(content, log_callback)

    compiled, separator_regex = load_pattern_search_rule(patterns_config, pattern_key)

    announce("[bold]>>> Searching files for matches and writing results to csv...[/bold]", log_callback)
    work(files, separator_regex, compiled, output_csv, convert_to_excel, log_callback)
