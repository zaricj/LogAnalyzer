import json
import os
import re
import shutil
import tempfile
from pathlib import Path
from typing import Any

from src.modules.io.file_utils import validate_file

# Flags every ``patterns`` regex is compiled with. The ``base`` regexes use none.
PATTERN_FLAGS = re.MULTILINE | re.DOTALL

# ========== Config ==========


def load_pattern_search_rule(patterns_config: Path, pattern_key: str) -> tuple[dict, re.Pattern]:
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
                re.compile(pattern_regex, PATTERN_FLAGS)
            except re.error as e:
                raise ValueError(
                    f"Invalid regex in pattern '{pattern_name}' for category '{category_name}': {e}"
                )

def load_patterns_json(filepath: Path) -> dict[str, Any]:
    with filepath.open("r", encoding="utf-8") as f:
        return json.load(f)


def save_patterns_json(filepath: Path, patterns_json: dict[str, Any], backup: bool = True) -> None:
    """Validate and write a patterns config atomically.

    The JSON is written to a temporary file in the target directory and then
    swapped in with ``os.replace``, so a crash mid-write never leaves a
    truncated config behind. With ``backup`` the previous file is kept as
    ``<name>.bak``.

    Raises:
        TypeError, ValueError: If ``patterns_json`` is not a valid config.
        OSError: If the file cannot be written.
    """
    validate_patterns_config(patterns_json)
    text = json.dumps(patterns_json, indent=2, ensure_ascii=False) + "\n"

    filepath.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp_name = tempfile.mkstemp(dir=filepath.parent, prefix=f".{filepath.name}.", suffix=".tmp")
    tmp_path = Path(tmp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
            f.flush()
            os.fsync(f.fileno())
        if backup and filepath.is_file():
            shutil.copy2(filepath, filepath.with_name(filepath.name + ".bak"))
        os.replace(tmp_path, filepath)
    finally:
        tmp_path.unlink(missing_ok=True)


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
        name: re.compile(p, PATTERN_FLAGS)
        for name, p in category_config.get("patterns", {}).items()
    }
    return compiled