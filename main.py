"""
Every single pattern key in patterns.json must contain a regex with multiple groups that will be used to search in an event block in log file.
This makes sure that a single line contains all the matches from the same event block.

'JSON' Expected structure:
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

from pathlib import Path
from datetime import datetime
from src.modules.core.pipeline import run_pipeline

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
        show_progress=True
    )

if __name__ == "__main__":
    main()
