"""Profile the search pipeline headlessly (same engine the GUI uses).

Run from the project root:  uv run python -m benchmark.main-profiling
or:                         uv run benchmark/main-profiling.py
"""

import cProfile
import pstats
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.models import PipelineEngine, SearchConfig  # noqa: E402


def main() -> None:
    output_dir = PROJECT_ROOT / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    config = SearchConfig(
        patterns_config=PROJECT_ROOT / "patterns" / "patterns.json",
        pattern_key="catalina_out_jasperserver",
        files_directory=PROJECT_ROOT / "logs",
        file_pattern="*.out",
        output_directory=output_dir,
        export_excel=True,
    )

    profiler = cProfile.Profile()
    profiler.enable()
    result = PipelineEngine().run(config)
    profiler.disable()

    print(
        f"{result.status.name}: {result.rows_written:,} rows from "
        f"{result.files_searched} file(s) in {result.elapsed_seconds:.2f}s"
    )

    profiler.dump_stats(output_dir / "profile.prof")
    with open(output_dir / "profile.txt", "w", encoding="utf-8") as f:
        stats = pstats.Stats(profiler, stream=f)
        stats.strip_dirs()
        stats.sort_stats("cumtime")
        stats.print_stats(50)


if __name__ == "__main__":
    main()
