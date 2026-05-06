from pathlib import Path
from re import Pattern
from typing import Callable
import time
import itertools
from src.modules.core.parser import collect_rows, get_headers_from_patterns
from src.modules.core.logging import announce, display_start_msg, display_finished_msg
from src.modules.io.config import load_pattern_search_rule
from src.modules.io.file_utils import get_files_in_folder
from src.modules.io.exporters import write_csv, convert_csv_to_excel

# ========== Pipeline ==========


def start_process(
    files: list[str],
    separator_regex: Pattern,
    compiled: Pattern,
    output_csv: Path,
    convert_to_excel: bool,
    log_callback: Callable,
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


    # Get headers from all patterns via their group names
    headers = get_headers_from_patterns(compiled)
    # Stitch the first row back together with the remaining generator
    full_generator = itertools.chain([first_row], row_generator)

    # Pass the stitched generator to the writer
    count = write_csv(output_csv, headers, full_generator)

    announce(
        f"[bold green]\n✓ Writing to csv has finished, wrote [bold yellow]{count}[/bold yellow] rows...\n[/bold green]",
        log_callback,
    )

    if convert_to_excel:  # Flag if conversion to excel should be done
        if count <= 1_048_576:
            excel_filename = output_csv.with_suffix(".xlsx")
            convert_csv_to_excel(
                output_csv, excel_filename, log_callback
            )  # Convert to excel
            announce(
                "[bold green]\n ✓ CSV converted to Excel![/bold green]",
                log_callback,
            )
        else:
            announce(
                "[bold yellow]\n ✖ CSV exceeds Excel's 1,048,576 row limit; Conversion to Excel is not possible.",
                log_callback,
            )
            excel_filename = ""

    end = time.time()
    total_time = f"{end - start:.2f}"
    content = display_finished_msg(
        str(output_csv), str(excel_filename), total_time, True, convert_to_excel
    )
    announce(content, log_callback)


def validate_ui_inputs(files_directory: Path) -> None:
    if str(files_directory).strip() == ".":
        raise ValueError("Directory path to search not provided.")


def execute_pipeline(
    patterns_config: Path,
    pattern_key: str,
    files_directory: Path,
    file_pattern: str,
    output_csv: Path,
    convert_to_excel: bool,
    log_callback: Callable[[str], None] = None,
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

    announce(
        "[bold]>>> Searching files for matches and writing results to csv...\n[/bold]",
        log_callback,
    )
    start_process(
        files, separator_regex, compiled, output_csv, convert_to_excel, log_callback
    )
