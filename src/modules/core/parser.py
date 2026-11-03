import re
from pathlib import Path

from src.modules.core.logging import announce
from src.modules.core.thread_executor import run_with_threading
from src.modules.core.timestamp import build_timestamp, extract_date_from_filename
from src.modules.io.file_utils import get_file_info

# ========== Yield one event block based on the separator pattern ==========


def yield_event_block(filepath, separator_pattern):
    if isinstance(separator_pattern, str):
        separator_pattern = re.compile(separator_pattern)

    buffer = []
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if separator_pattern.match(line) and buffer:
                yield "".join(buffer)
                buffer.clear()
            buffer.append(line)

    if buffer:
        yield "".join(buffer)


# ========= Extract matches from event blocks =========


def extract_matches_from_event_block(
    event_block: str, compiled_patterns: dict
) -> dict[str, str]:
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

    # Process "base" patterns (e.g., time/separator info)
    for regex in compiled_patterns.get("base", {}).values():
        match = regex.search(event_block)
        if match:
            for key, value in match.groupdict().items():
                # Only set if the key is new or current value is empty
                if value and not row.get(key):
                    row[key] = value

    # Process "patterns" (the specific match extractors)
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


def collect_rows(files: list, separator_regex, compiled, log_callback):
    """Collect rows from files, applying keyword filtering and optimizing timestamping."""
    files_info = run_with_threading(get_file_info, files)
    for file in files_info:
        if not file:
            continue

        filepath: Path = file["Filepath"]

        # CACHE these values once per file
        date_created = file["Created"].split("-")[0].strip()
        filename_date = extract_date_from_filename(filepath) or date_created
        announce(f"> Searching file [bold magenta]{filepath}[/bold magenta]...", log_callback)
        
        block_iter = yield_event_block(filepath, separator_regex)

        for block in block_iter:
            matches = extract_matches_from_event_block(block, compiled)
            
            if not matches:
                continue
            
            parsed_time = matches.get("time")
            if parsed_time:
                matches["timestamp"] = build_timestamp(parsed_time, filename_date)
            # Ensure 'time' is removed only after processing all matches in this block
            if "time" in matches:
                matches.pop("time")
            # Validate row is not empty after processing
            if not has_data(matches, "timestamp"):
                continue

            # Yield each valid row immediately
            yield matches


def has_data(row: dict, ignore_key: str) -> bool:
	return any(v not in (None, "", "null") for k, v in row.items() if k != ignore_key)


def get_headers_from_patterns(compiled: dict) -> list[str]:
    """Extract all named groups from compiled patterns to build complete headers."""
    seen = set()
    headers = ["timestamp"]
    for group in ("base", "patterns"):
        for regex in compiled.get(group, {}).values():
            for name in regex.groupindex:
                if name not in ("time", "timestamp") and name not in seen:
                    seen.add(name)
                    headers.append(name)
    return headers


def clean_block(block: str, ignore_regex: re.Pattern) -> str:
    block = ignore_regex.sub("", block)
    block = re.sub(r"\n{2,}", "\n", block)
    return block.strip()
