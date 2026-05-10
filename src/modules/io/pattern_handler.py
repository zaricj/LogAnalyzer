import re
from pathlib import Path

from modules.core.utils import load_patterns_json, compile_regex_patterns
from modules.io.file_utils import validate_file

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
