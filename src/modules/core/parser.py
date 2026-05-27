import re
from pathlib import Path
from typing import Dict
from rich.progress import (
    Progress,
    TextColumn,
    BarColumn,
    TaskProgressColumn,
    TimeRemainingColumn,
)

from src.modules.core.timestamp import build_timestamp, extract_date_from_filename
from src.modules.utility.thread_executor import run_with_threading
from src.modules.io.file_utils import get_file_info

# ========== Yield one event block based on the separator pattern ==========


def yield_event_block(filepath, separator_pattern, progress=None, task_id=None):
    if isinstance(separator_pattern, str):
        separator_pattern = re.compile(separator_pattern)

    buffer = []
    line_count = 0
    
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line_count += 1
            
            # Only update UI every 1000 lines
            if progress and task_id is not None and line_count % 1000 == 0:
                progress.advance(task_id, 1000)
                line_count = 0  # Reset

            if separator_pattern.match(line):
                if buffer:
                    yield "".join(buffer)
                    buffer.clear()
            buffer.append(line)

    # Clean up any leftover line count for the final progress push
    if progress and task_id is not None and line_count > 0:
        progress.advance(task_id, line_count)

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


def get_headers_from_patterns(compiled: dict) -> list[str]:
    """Extract all named groups from compiled patterns to build complete headers."""
    seen = set()
    headers = ["timestamp"]
    for group in ("base", "patterns"):
        for _, regex in compiled.get(group, {}).items():
            for name in regex.groupindex.keys():
                if name not in ("time", "timestamp") and name not in seen:
                    seen.add(name)
                    headers.append(name)
    return headers


def is_keyword_event(keyword: str, event_block: str) -> bool:
    """Use this to filter out event blocks that contain a specific keyword

    Args:
        keyword (str): Keyword to look for in event block
        event_block (str): Event text block in the log file

    Returns:
        bool: True if keyword is in the event block, False otherwise
    """
    return keyword.lower() in event_block.lower()


def clean_block(block: str, ignore_regex: re.Pattern) -> str:
    block = ignore_regex.sub("", block)
    block = re.sub(r"\n{2,}", "\n", block)
    return block.strip()
