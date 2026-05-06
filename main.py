from pathlib import Path
from datetime import datetime
from src.modules.core.pipeline import run_pipeline


def main() -> None:
    # Search patterns config
    PATTERNS_CONFIG = "src/patterns/patterns.json"
    PATTERN_KEY = "sql_exceptions"

    # File(s) to search config
    FILES_DIR = "test"
    FILE_PATTERN = "sample.log"

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
