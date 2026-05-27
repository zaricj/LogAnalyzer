import cProfile
import pstats
from pathlib import Path
from datetime import datetime
from src.modules.core.pipeline import run_pipeline


def main() -> None:
    WORKING_DIR: Path = Path.cwd()

    PATTERNS_CONFIG: Path = WORKING_DIR / "patterns" / "patterns.json"
    PATTERN_KEY = "catalina_out_jasperserver"

    FILES_DIR: Path = Path(r"logs")
    FILE_PATTERN = "*.out"

    OUTPUT_DIR: Path = Path("output")
    TIMESTAMP_PREFIX = datetime.now().strftime("%Y_%m_%d")
    CSV_FILE: Path = OUTPUT_DIR / f"{TIMESTAMP_PREFIX}_{PATTERN_KEY}.csv"

    PROFILE_FILE = OUTPUT_DIR / "profile.prof"
    TEXT_REPORT = OUTPUT_DIR / "profile.txt"

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    profiler = cProfile.Profile()
    profiler.enable()

    run_pipeline(
        patterns_config=PATTERNS_CONFIG,
        pattern_key=PATTERN_KEY,
        files_directory=FILES_DIR,
        file_pattern=FILE_PATTERN,
        output_csv=CSV_FILE,
        event_keyword="",
        show_progress=True,
    )

    profiler.disable()
    profiler.dump_stats(PROFILE_FILE)

    # Convert to human-readable text
    with open(TEXT_REPORT, "w", encoding="utf-8") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs()
        stats.sort_stats("cumtime")   # or "tottime"
        stats.print_stats(50)         # top 50 functions


if __name__ == "__main__":
    main()