import json
import re
from pathlib import Path


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
