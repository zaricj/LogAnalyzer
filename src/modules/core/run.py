from pathlib import Path
import time
import itertools

from src.modules.core.ui import RPRINT, display_start_msg, display_finished_msg
from src.modules.core.parser import collect_rows, get_headers_from_patterns
from src.modules.io.regex_service import load_pattern_search_rule
from src.modules.io.file_utils import get_files_in_folder
from src.modules.io.exporters import write_csv, convert_csv_to_excel


# ========== Pipeline ==========


def start_search_task(
    files, separator_regex, compiled, output_csv, event_keyword, show_progress
):
    start = time.time()  # Process start time
    excel_filename = ""
    # Get headers from all patterns via their group names
    headers = get_headers_from_patterns(compiled)

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

    # Stitch the first row back together with the remaining generator
    full_generator = itertools.chain([first_row], row_generator)

    # Pass the stitched generator to the writer
    count = write_csv(output_csv, headers, full_generator)
    RPRINT(
        f"[bold green]✓ Writing to csv has finished, wrote [bold yellow]{count}[/bold yellow] rows...[/bold green]"
    )

    if count <= 1_048_576:
        excel_filename = output_csv.with_suffix(".xlsx")
        convert_csv_to_excel(output_csv, excel_filename)  # Convert to excel
        RPRINT("[bold green]✓ CSV converted to excel format.[/bold green]")
    else:
        RPRINT(
            "[bold yellow]✖ CSV exceeds Excel's 1,048,576 row limit; Conversion to Excel is not possible."
        )

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
        patterns_config, 
        pattern_key,
        files_directory,
        file_pattern,
        event_keyword)

    files = get_files_in_folder(files_directory, file_pattern)
    if not files:
        raise ValueError(
            f"No files found in {files_directory}, using pattern {file_pattern}"
        )

    compiled, separator_regex = load_pattern_search_rule(patterns_config, pattern_key)

    RPRINT("[bold]>>> Searching files for matches and writing results to csv...[/bold]")

    start_search_task(
        files, separator_regex, compiled, output_csv, event_keyword, show_progress
    )
