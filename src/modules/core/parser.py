import re
from pathlib import Path
from typing import Any, Callable, Dict, Iterable, Iterator
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

# Number of lines between two progress notifications while streaming a file.
PROGRESS_LINE_STEP = 1000

LinesCallback = Callable[[int], None]
FileStartCallback = Callable[[int, dict[str, Any]], None]

# ========== Yield one event block based on the separator pattern ==========


def yield_event_block(
    filepath: Path,
    separator_pattern: re.Pattern | str,
    on_lines: LinesCallback | None = None,
) -> Iterator[str]:
    """Stream a file and yield one event block per separator match.

    Args:
        filepath: File to read.
        separator_pattern: Regex marking the first line of a new event block.
        on_lines: Optional callback receiving the number of lines processed since
            the last call (invoked every ``PROGRESS_LINE_STEP`` lines and once at EOF).
    """
    if isinstance(separator_pattern, str):
        separator_pattern = re.compile(separator_pattern)

    buffer: list[str] = []
    line_count = 0

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line_count += 1

            # Only notify every PROGRESS_LINE_STEP lines
            if on_lines is not None and line_count == PROGRESS_LINE_STEP:
                on_lines(line_count)
                line_count = 0

            if separator_pattern.match(line) and buffer:
                yield "".join(buffer)
                buffer.clear()
            buffer.append(line)

    # Flush any leftover line count for the final progress push
    if on_lines is not None and line_count > 0:
        on_lines(line_count)

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
    for regex in compiled_patterns.get("base", {}).values():
        match = regex.search(event_block)
        if match:
            for key, value in match.groupdict().items():
                # Only set if the key is new or current value is empty
                if value and not row.get(key):
                    row[key] = value

    # 2. Process "patterns" (the specific match extractors)
    for regex in compiled_patterns.get("patterns", {}).values():
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

def iter_rows_from_files(
    files_info: Iterable[dict[str, Any]],
    separator_regex: re.Pattern,
    compiled: dict,
    keyword: str,
    on_file_start: FileStartCallback | None = None,
    on_lines: LinesCallback | None = None,
) -> Iterator[dict[str, str]]:
    """UI-agnostic row generator: search every file and yield one dict per matching event.

    Args:
        files_info: File info dicts as produced by ``get_file_info``.
        separator_regex: Compiled event separator regex.
        compiled: Compiled ``base``/``patterns`` regex dictionary.
        keyword: Optional case-insensitive keyword an event block must contain.
        on_file_start: Called with ``(index, file_info)`` before a file is searched.
        on_lines: Called with the number of lines processed (see ``yield_event_block``).
    """
    # Pre-compile keyword regex to avoid .lower() on every block
    keyword_re = re.compile(re.escape(keyword), re.IGNORECASE) if keyword else None

    for index, file in enumerate(files_info):
        if not file:
            continue

        filepath: Path = file["Filepath"]
        if on_file_start is not None:
            on_file_start(index, file)

        # CACHE these values once per file
        # Quick fix: Split on space to grab just the date part (e.g., "2026-01-19")
        date_created = file["Created"].split(" ")[0].strip()
        filename_date = extract_date_from_filename(filepath) or date_created

        for block in yield_event_block(filepath, separator_regex, on_lines):
            if keyword_re and not keyword_re.search(block):
                continue

            matches = extract_matches_from_event_block(block, compiled)

            if not matches:
                continue

            parsed_time = matches.get("time")
            if parsed_time:
                # Run the blazing fast string translation function
                matches["timestamp"] = build_timestamp(parsed_time, filename_date)

            # Cleanup 'time' key so it doesn't pollute the CSV headers
            matches.pop("time", None)

            # Validate row is not empty after processing
            if not has_data(matches, "timestamp"):
                continue

            # Yield each valid row immediately
            yield matches


def collect_rows(
    files: list, separator_regex, compiled, keyword: str, show_progress: bool
):
    """Collect rows from files with rich progress bars (CLI front-end for ``iter_rows_from_files``)."""
    files_info = run_with_threading(get_file_info, files)

    with Progress(
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        TimeRemainingColumn(),
        transient=False,  # Bars do not disappear when finished
    ) as progress:
        current_task: dict[str, Any] = {"id": None}

        def on_file_start(_: int, file: dict[str, Any]) -> None:
            if show_progress:
                current_task["id"] = progress.add_task(
                    f"Searching [bold magenta]{file['Filepath'].name}[/bold magenta]...",
                    total=file["Lines"],
                )

        def on_lines(count: int) -> None:
            if current_task["id"] is not None:
                progress.advance(current_task["id"], count)

        yield from iter_rows_from_files(
            files_info, separator_regex, compiled, keyword, on_file_start, on_lines
        )


def has_data(row: dict, ignore_key: str) -> bool:
    return any(v not in (None, "", "null") for k, v in row.items() if k != ignore_key)


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
