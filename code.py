from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)
from rich import print as rprint

from concurrent.futures import ThreadPoolExecutor
from typing import Callable, Iterable, Dict, TextIO, Any, Iterator
import os
import pandas as pd
import csv
import itertools
import time
import json
import re

# ========== Load & Compile Patterns ==========


def load_patterns_json(filepath: Path) -> dict[str, str]:
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def get_pattern_keys(filepath: Path) -> list[str]:
    patterns = load_patterns_json(filepath)
    return list(patterns.keys())


def compile_regex(pattern: str, flags=0):
    return re.compile(pattern, flags)


def compile_regex_patterns(category_config: dict):
    """Compile base separator + patterns for one category"""
    compiled = {}
    compiled["base"] = {
        name: re.compile(p) for name, p in category_config.get("base", {}).items()
    }
    compiled["patterns"] = {
        name: re.compile(p, re.MULTILINE | re.DOTALL)
        for name, p in category_config.get("patterns", {}).items()
    }
    return compiled


def write_csv(output: Path, headers: list[str], rows: Iterator[dict]) -> int:
    """Writes rows to a CSV file with the specified headers.

    Args:
        output (Path): The path to the output CSV file.
        headers (list[str]): A list of column headers for the CSV.
        rows (Iterator[dict]): An iterator over dictionaries representing each row.

    Returns:
        int: The number of rows written to the CSV file.
    """
    count = 0

    if not output.parent.exists():
        ensure_output_dir(output)

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=headers, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
        )
        writer.writeheader()

        for row in rows:
            normalized = {k: row.get(k, "") for k in headers}
            writer.writerow(normalized)
            count += 1

    return count


# ========== Excel Conversion ==========


def convert_csv_to_excel(input_csv_file: Path, output_excel_file: Path):
    if not input_csv_file.exists():
        raise FileNotFoundError("Invalid input file.")

    chunk_size = 1024

    with Console.status("[bold]>>> Converting CSV to Excel...[/bold]", spinner="arc"):
        # read_csv is significantly faster than the csv module for large files
        csv_reader = pd.read_csv(
            input_csv_file,
            sep=";",
            quotechar='"',
            encoding="utf-8",
            engine="c",
            chunksize=chunk_size,
        )

        # Using ExcelWriter to handle sequential writing
        with pd.ExcelWriter(output_excel_file, engine="xlsxwriter") as writer:
            for i, chunk in enumerate(csv_reader):
                write_header = i == 0
                start_row = i * chunk_size
                # to_excel handles all type conversions (ints, floats, strings) natively
                chunk.to_excel(
                    writer,
                    sheet_name="Result",
                    startrow=start_row,
                    index=False,
                    header=write_header,
                )


# ===== Validation ====== #


def validate_file(file: Path) -> bool:
    try:
        # First check if file is not None
        if not file:
            raise ValueError("No file provided for processing.")

        # If not None, check if file exists
        if not file.exists():
            raise FileNotFoundError(f"The specified file '{file}' does not exist.")
        else:
            return True
    except FileNotFoundError:
        return False


def count_lines(filepath: Path) -> int:
    # Source - https://stackoverflow.com/a/9631635
    # Posted by glglgl, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-04-07, License - CC BY-SA 3.0

    def blocks(file: TextIO, size: int = 65536):
        while True:
            b = file.read(size)
            if not b:
                break
            yield b

    with open(filepath, "rb") as f:
        return sum(bl.count(b"\n") for bl in blocks(f))


def get_files_in_folder(directory: Path, file_pattern: str = "*.log") -> list[Path]:
    """Get files from a directory, of specific type

    Args:
        directory (Path): Path to the folder that contains files
        file_pattern (str, optional): Only get files that match this pattern. Defaults to "*.log".

    Returns:
        list[Path]: List of found files in the directory.
    """
    if directory.is_dir() and directory.exists():
        return list(directory.glob(file_pattern))
    else:
        return []


def ensure_output_dir(directory: Path):
    Path.mkdir(directory.parent, exist_ok=True)
    print(f"Created directory successfully: '{directory.__str__()}'")


def epoch_to_timestamp(epoch_time: float) -> str:
    """
    Converts epoch time (in seconds) and formats it as DD.MM.YYYY - HH:MM:SS.

    Args:
        epoch_time_sec: The epoch time in seconds.

    Returns:
        A string representing the formatted date,
        or an error message if the input is invalid.
    """
    try:
        # Create a datetime object from the epoch time
        dt_object = datetime.fromtimestamp(epoch_time)
        # Format the datetime object as DD.MM.YYYY - HH:MM:SS
        formatted_time = dt_object.strftime("%d.%m.%Y - %H:%M:%S")
        return formatted_time
    except (TypeError, ValueError) as e:
        return f"Error: Invalid epoch time provided. {e}"


# ===== File information grabbers


def get_file_size(filepath: Path) -> int:
    return filepath.stat().st_size


def get_file_created_on_date(filepath: Path) -> str:
    file_created_on = epoch_to_timestamp(filepath.stat().st_birthtime)
    return file_created_on


def get_file_info(filepath: Path) -> dict[str, Any]:
    try:
        stat = filepath.stat()
        data = {
            "Filepath": filepath,
            "Size": stat.st_size,
            "Created": epoch_to_timestamp(stat.st_birthtime),
            "Modified": epoch_to_timestamp(stat.st_mtime),
            "Lines": count_lines(filepath),
        }
        return data
    except Exception:
        return {}


_MONTH_MAP = {
    "Jan": "Jan",
    "Feb": "Feb",
    "Mar": "Mär",
    "Apr": "Apr",
    "May": "Mai",
    "Jun": "Jun",
    "Jul": "Jul",
    "Aug": "Aug",
    "Sep": "Sep",
    "Oct": "Okt",
    "Nov": "Nov",
    "Dec": "Dez",
}

_DATETIME_FORMATS = [
    "%d/%b/%Y:%H:%M:%S",  # 15/Apr/2026:00:00:10 (localhost https-request logs)
    "%d-%b-%Y %H:%M:%S.%f",  # 19-Jan-2026 06:48:33.088  (Tomcat SEVERE)
    "%d-%b-%Y %H:%M:%S",  # 19-Jan-2026 06:48:33
    "%Y-%m-%dT%H:%M:%S,%f",  # 2026-01-19T07:33:23,289   (ISO 8601, comma ms)
    "%Y-%m-%dT%H:%M:%S.%f",  # 2026-01-19T07:33:23.289   (ISO 8601, dot ms)
    "%Y-%m-%dT%H:%M:%S",  # 2026-01-19T07:33:23
    "%Y-%m-%d %H:%M:%S,%f",  # 2026-01-19 07:33:23,289
    "%Y-%m-%d %H:%M:%S.%f",  # 2026-01-19 07:33:23.289
    "%Y-%m-%d %H:%M:%S",  # 2026-01-19 07:33:23
]

# Patterns that represent a FULL datetime (date + time already present)
_FULL_DATETIME_PATTERNS = [
    # 19-Jan-2026 06:48:33.088
    re.compile(r"\d{1,2}-[A-Za-z]{3}-\d{4}\s+\d{2}:\d{2}:\d{2}"),
    # 2026-01-19T07:33:23,289  or  2026-01-19 07:33:23
    re.compile(r"\d{4}-\d{2}-\d{2}[T\s]\d{2}:\d{2}:\d{2}"),
    # 15/Apr/2026:06:15:40
    re.compile(r"\d{1,2}/[A-Za-z]{3}/\d{4}:\d{2}:\d{2}:\d{2}"),
    # Add more formats if needed
]

# Matches a bare time: 06:48:33 or 06:48:33.088 or 06:48:33,289
_TIME_ONLY_RE = re.compile(r"^\d{2}:\d{2}:\d{2}")
_FILENAME_DATE_RE = re.compile(r"\d{4}[-_.]\d{2}[-_.]\d{2}")


def is_full_datetime(time_str: str) -> bool:
    """Return True if the string already contains a date component."""
    return any(p.search(time_str) for p in _FULL_DATETIME_PATTERNS)


def extract_date_from_filename(filepath: Path) -> str:
    """Uses pre-compiled regex and avoids redundant Path ops."""
    match = _FILENAME_DATE_RE.search(filepath.name)
    if match:
        return match.group().replace("_", "-").replace(".", "-")
    return ""


def to_german_datetime(time_str: str) -> str:
    t = time_str.strip()
    for fmt in _DATETIME_FORMATS:
        try:
            dt = datetime.strptime(t, fmt)
            month_de = _MONTH_MAP.get(dt.strftime("%b"), dt.strftime("%b"))
            return dt.strftime(f"%d. {month_de} %Y %H:%M:%S")
        except ValueError:
            continue
    return t


def build_timestamp(time_str: str, cached_date: str) -> str:
    """
    Accepts a pre-calculated date string instead of a Path object
    to avoid per-row disk/string logic.
    """
    t = time_str.strip()
    if is_full_datetime(t):
        return to_german_datetime(t)  # Already complete, nothing to add

    # Check if t already looks like a full date (e.g. starts with 2026 or 15/)
    # if len(t) > 10 and (t[4] == "-" or t[2] == "/" or t[2] == "-"):
    #     return to_german_datetime(t)

    if _TIME_ONLY_RE.match(t):
        return to_german_datetime(f"{cached_date} {t}")

    return to_german_datetime(f"{cached_date} {t}") if t else cached_date


def yield_event_block(filepath, separator_pattern, progress=None, task_id=None):
    if isinstance(separator_pattern, str):
        separator_pattern = re.compile(separator_pattern)

    buffer = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            # Update the progress bar every line
            if progress and task_id is not None:
                progress.advance(task_id)

            if separator_pattern.match(line):
                if buffer:
                    yield "".join(buffer)
                    buffer.clear()
            buffer.append(line)

    if buffer:
        yield "".join(buffer)


# ========= Extract matches from event blocks =========


def extract_matches_from_event_block(
    event_block: str, compiled_patterns: dict
) -> Dict[str, str]:
    """Extract the matches from the event block of text, with the compiled regex patterns.
    Uses a non-destructive update: later patterns will not overwrite keys already
    found by earlier patterns.

    Args:
        event_block (str): The text block of the event.
        compiled_patterns (dict): A dictionary of compiled regex patterns.

    Returns:
        dict: A dictionary containing the found matches in the event block.
    """
    row = {}

    # 1. Process "base" patterns (e.g., time/separator info)
    for _, regex in compiled_patterns.get("base", {}).items():
        match = regex.search(event_block)
        if match:
            for key, value in match.groupdict().items():
                # Only set if the key is new or current value is empty
                if value and not row.get(key):
                    row[key] = value

    # 2. Process "patterns" (the specific match extractors)
    for _, regex in compiled_patterns.get("patterns", {}).items():
        match = regex.search(event_block)
        if match:
            new_data = match.groupdict()
            for key, value in new_data.items():
                # NON-DESTRUCTIVE: Keep the first non-empty value found
                # If match was found by pattern A, pattern B won't overwrite it.
                if value and not row.get(key):
                    row[key] = value

    return row


# ========== Rows and headers Generator ==========

"""
Threading sample usage:

    files = get_files_in_folder("logs")
    
    # Use executor.map() to parallelize work on multiple files
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(file_info, files))
        
    # Do something with the results list
"""


def run_with_threading(
    func: Callable, iterable: Iterable, max_workers: int = None
) -> list:
    """Runs a function in parallel on an iterable of inputs using a thread pool.
    Args:
        func (callable): The function to be executed in parallel.
        iterable (iterable): The collection of inputs to pass to the function.
        max_workers (int, optional): The maximum number of threads to use. Defaults to None, which means the number of threads is determined by the system.
    Returns:
        list: A list of results from executing the function on each input in the iterable.

    Raises:
        Exception: Any exception raised by the function being executed.
    """
    if max_workers is None:
        max_workers = min(32, (os.cpu_count() or 1) * 5)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        return list(executor.map(func, iterable))


def collect_rows(
    files: list, separator_regex, compiled, keyword: str, show_progress: bool
):
    """Collect rows from files, applying keyword filtering and optimizing timestamping."""
    files_info = run_with_threading(get_file_info, files)

    # Pre-compile keyword regex to avoid .lower() on every block
    keyword_re = re.compile(re.escape(keyword), re.IGNORECASE) if keyword else None
    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        transient=False,  # Bars do not disappear when finished
    ) as progress:
        for file in files_info:
            if not file:
                continue

            filepath: Path = file["Filepath"]
            task_id = (
                progress.add_task(
                    f"Searching [bold magenta]{filepath.name}[/bold magenta]...",
                    total=file["Lines"],
                )
                if show_progress
                else None
            )

            # CACHE these values once per file
            date_created = file["Created"].split("-")[0].strip()
            filename_date = extract_date_from_filename(filepath) or date_created

            # rprint(f"Processing: [bold blue]{filepath.name}[/bold blue]")

            block_iter = yield_event_block(filepath, separator_regex, progress, task_id)

            for block in block_iter:
                if keyword_re and not keyword_re.search(block):
                    continue

                matches = extract_matches_from_event_block(block, compiled)

                if not matches:
                    continue

                parsed_time = matches["time"]
                if parsed_time:
                    matches["timestamp"] = build_timestamp(parsed_time, filename_date)
                # Ensure 'time' is removed only after processing all matches in this block
                if "time" in matches:
                    matches.pop("time")
                # Validate row is not empty after processing
                if not is_empty_row(matches, "timestamp"):
                    continue

                # Yield each valid row immediately
                yield matches


def is_empty_row(row: dict, ignore_key: str) -> bool:
    # Filter empty rows (ignore timestamp)
    return any(v not in (None, "") for k, v in row.items() if k != ignore_key)


def collect_headers(row: dict) -> list:
    return [key for key in row.keys()]


def is_keyword_event(keyword: str, event_block: str) -> bool:
    """Use this to filter out event blocks that contain a specific keyword

    Args:
        keyword (str): Keyword to look for in event block
        event_block (str): Event text block in the log file

    Returns:
        bool: True if keyword is in the event block, False otherwise
    """
    return keyword.lower() in event_block.lower()


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
    Console.print(panel)


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
    Console.print(panel)


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

    # ========== Config ==========


def load_pattern_search_rule(
    patterns_config: Path, pattern_key: str
) -> tuple[dict, re.Pattern]:
    """Load the selected pattern `JSON` file which contains the regex ruleset for searching

    Args:
        patterns_config (Path): The `JSON` pattern configuration file which contains all regex search rules.
        pattern_key (str): The main pattern rule key to use for searching.

    Raises:
        FileNotFoundError: If the pattern `JSON` file does not exist.
        ValueError: If an non existent pattern rule key has been selected.

    Returns:
        tuple[dict, re.Pattern]: The compiled pattern rule's regexes and the separator regex for event blocks.
    """
    # Validate if patterns config exists
    if not validate_file(patterns_config):
        raise FileNotFoundError(f"Patterns config file not found: {patterns_config}")

    # Load and validate patterns JSON
    patterns_json = load_patterns_json(patterns_config)
    validate_patterns_config(patterns_json)

    # Validate pattern_key exists
    if pattern_key not in patterns_json:
        raise ValueError(
            f"Invalid pattern key: '{pattern_key}'. Available keys: {list(patterns_json.keys())}"
        )

    # Compile patterns for the selected category
    compiled = compile_regex_patterns(patterns_json[pattern_key])
    separator_regex = compiled["base"]["separator"]

    return compiled, separator_regex


def validate_patterns_config(patterns_json: dict[str, dict[str, dict[str, str]]]):
    """
    Validate the structure and content of the patterns JSON.

    Expected structure:
    >>> {
        "category_name": {
            "base": {
                "separator": "regex_string"
            },
            "patterns": {
                "pattern_name": "regex_string",
                ...
            }
        },
        ...
    }
    """
    if not isinstance(patterns_json, dict):
        raise TypeError("patterns_json must be a dictionary")

    for category_name, category_config in patterns_json.items():
        if not isinstance(category_config, dict):
            raise TypeError(f"Category '{category_name}' must be a dictionary")

        # Check required keys
        if "base" not in category_config:
            raise ValueError(f"Category '{category_name}' missing 'base' section")
        if "patterns" not in category_config:
            raise ValueError(f"Category '{category_name}' missing 'patterns' section")

        # Validate base section
        base = category_config["base"]
        if not isinstance(base, dict):
            raise TypeError(
                f"'base' in category '{category_name}' must be a dictionary"
            )
        if "separator" not in base:
            raise ValueError(
                f"'base' in category '{category_name}' missing 'separator'"
            )
        if not isinstance(base["separator"], str):
            raise TypeError(
                f"'separator' in category '{category_name}' must be a string"
            )

        # Validate patterns section
        patterns = category_config["patterns"]
        if not isinstance(patterns, dict):
            raise TypeError(
                f"'patterns' in category '{category_name}' must be a dictionary"
            )
        for pattern_name, pattern_regex in patterns.items():
            if not isinstance(pattern_regex, str):
                raise TypeError(
                    f"Pattern '{pattern_name}' in category '{category_name}' must be a string"
                )

        # Validate regex compilation
        try:
            re.compile(base["separator"])
        except re.error as e:
            raise ValueError(
                f"Invalid regex in 'separator' for category '{category_name}': {e}"
            )

        for pattern_name, pattern_regex in patterns.items():
            try:
                re.compile(pattern_regex, re.MULTILINE | re.DOTALL)
            except re.error as e:
                raise ValueError(
                    f"Invalid regex in pattern '{pattern_name}' for category '{category_name}': {e}"
                )


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


def main() -> None:
    # Search patterns config
    PATTERNS_CONFIG = "src/patterns/patterns.json"
    PATTERN_KEY = "catalina_out_jasperserver"

    # File(s) to search config
    FILES_DIR = "logs"
    FILE_PATTERN = "*.txt"

    # CSV output
    OUTPUT_DIR = "output"
    TIMESTAMP_PREFIX = datetime.now().strftime("%Y_%m_%d")
    CSV_FILE = f"{OUTPUT_DIR}/{TIMESTAMP_PREFIX}_{PATTERN_KEY}.csv"

    run_pipeline(
        patterns_config=Path(PATTERNS_CONFIG),
        pattern_key=PATTERN_KEY,
        files_directory=Path(FILES_DIR),
        file_pattern=FILE_PATTERN,
        output_csv=Path(CSV_FILE),
        event_keyword="",
        show_progress=True,
    )


if __name__ == "__main__":
    main()
