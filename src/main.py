from pathlib import Path
from datetime import datetime
from modules.core.pipeline import run_pipeline

def main() -> None:
    
    # Current working directory
    WORKING_DIR: Path = Path.cwd()
    
    # Search patterns config
    PATTERNS_CONFIG: Path = WORKING_DIR / "patterns" / "patterns.json"
    PATTERN_KEY = "catalina_out_jasperserver"

    # File(s) to search config
    FILES_DIR: Path = Path(r"C:\Users\ZaricJ\Downloads")
    FILE_PATTERN = "*.out"

    # CSV output
    OUTPUT_DIR: Path = Path("output")
    TIMESTAMP_PREFIX = datetime.now().strftime("%Y_%m_%d")
    CSV_FILE: Path = Path(f"{OUTPUT_DIR}/{TIMESTAMP_PREFIX}_{PATTERN_KEY}.csv")

    run_pipeline(
        patterns_config=PATTERNS_CONFIG,
        pattern_key=PATTERN_KEY,
        files_directory=FILES_DIR,
        file_pattern=FILE_PATTERN,
        output_csv=CSV_FILE,
        event_keyword="",
        show_progress=True,
    )

if __name__ == "__main__":
    main()
