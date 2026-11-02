from datetime import datetime
from pathlib import Path
from typing import Annotated
import typer

from src.modules.core.run import run_pipeline
from src.modules.io.regex_service import get_pattern_keys

# ===== Constants =====
WORKING_DIR: Path = Path.cwd()
PATTERNS_CONFIG_FILE: Path = WORKING_DIR / "patterns" / "patterns.json"

app = typer.Typer(
    help="Glint ✨ - A file analysis and pattern extraction tool with regex.",
    add_completion=False,
)


@app.command()
def run(
    patterns_config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to the patterns JSON configuration file.",
        ),
    ] = PATTERNS_CONFIG_FILE,
    pattern_key: Annotated[
        str,
        typer.Option(
            "--pattern",
            "-p",
            help="Pattern key to use for searching (Mandatory). Use command 'patterns' to get all available patterns.",
        ),
    ] = ...,
    files_directory: Annotated[
        Path,
        typer.Option(
            "--dir",
            "-d",
            help="Path to the directory containing the text files to be searched.",
        ),
    ] = ...,
    file_pattern: Annotated[
        str,
        typer.Option(
            "--file-pattern",
            "-fp",
            help="File glob pattern to match.",
        ),
    ] = "*.log",
    output_dir: Annotated[
        Path,
        typer.Option(
            "--outdir",
            "-o",
            help="Directory where generated CSV and Excel reports will be saved (Mandatory).",
        ),
    ] = ...,
    event_keyword: Annotated[
        str,
        typer.Option(
            "--keyword",
            "-k",
            help="Optional event keyword filter.",
        ),
    ] = "",
    show_progress: Annotated[
        bool,
        typer.Option(
            "--progress/--no-progress",
            help="Show rich progress bars during file searching.",
        ),
    ] = True,
) -> None:
    """Run the Glint file parsing and report generation pipeline."""
    timestamp_prefix = datetime.now().strftime("%Y_%m_%d")
    output_csv = output_dir / f"{timestamp_prefix}_{pattern_key}.csv"

    run_pipeline(
        patterns_config=patterns_config,
        pattern_key=pattern_key,
        files_directory=files_directory,
        file_pattern=file_pattern,
        output_csv=output_csv,
        event_keyword=event_keyword,
        show_progress=show_progress,
    )


@app.command(name="patterns")
def list_patterns(
    patterns_config: Annotated[
        Path,
        typer.Option(
            "--config",
            "-c",
            help="Path to the patterns JSON configuration file.",
        ),
    ] = PATTERNS_CONFIG_FILE,
) -> None:
    """List all available pattern keys defined in the configuration file."""
    try:
        keys = get_pattern_keys(patterns_config)
        typer.echo(f"\n[Available Pattern Keys in {patterns_config}]")
        for key in keys:
            typer.echo(f"  • {key}")
        typer.echo("")
    except Exception as e:
        typer.echo(f"[red]Error loading pattern keys: {e}[/red]")


if __name__ == "__main__":
    app()
