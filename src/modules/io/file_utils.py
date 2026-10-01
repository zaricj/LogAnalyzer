from pathlib import Path
from typing import Any, TextIO

from src.modules.io.converters import epoch_to_timestamp

# ===== Validation ====== #


def validate_file(file: Path) -> bool:
    try:
        # First check if file is not None
        if not file:
            raise ValueError("No file provided for processing.")

        # If not None, check if file exists
        if not file.exists():
            raise FileNotFoundError(f"The specified file '{file}' does not exist.")
        else:
            return True
    except FileNotFoundError:
        return False


def count_lines(filepath: Path) -> int:
    # Source - https://stackoverflow.com/a/9631635
    # Posted by glglgl, modified by community. See post 'Timeline' for change history
    # Retrieved 2026-04-07, License - CC BY-SA 3.0

    def blocks(file: TextIO, size: int = 65536):
        while True:
            b = file.read(size)
            if not b:
                break
            yield b

    with open(filepath, "rb") as f:
        return sum(bl.count(b"\n") for bl in blocks(f))


def get_files_in_folder(directory: Path, file_pattern: str = "*.log") -> list[Path]:
    """Get files from a directory, of specific type

    Args:
        directory (Path): Path to the folder that contains files
        file_pattern (str, optional): Only get files that match this pattern. Defaults to "*.log".

    Returns:
        list[Path]: List of found files in the directory.
    """
    if directory.is_dir() and directory.exists():
        return list(directory.glob(file_pattern))
    else:
        return []


def ensure_output_dir(directory: Path):
    Path.mkdir(directory.parent, exist_ok=True)
    print(f"Created directory successfully: '{directory.__str__()}'")


# ===== File information grabbers


def get_file_size(filepath: Path) -> int:
    return filepath.stat().st_size


def get_file_created_on_date(filepath: Path) -> str:
    file_created_on = epoch_to_timestamp(filepath.stat().st_birthtime)
    return file_created_on


def get_file_info(filepath: Path) -> dict[str, Any]:
    try:
        stat = filepath.stat()
        data = {
            "Filepath": filepath,
            "Size": stat.st_size,
            "Created": epoch_to_timestamp(stat.st_birthtime),
            "Modified": epoch_to_timestamp(stat.st_mtime),
            "Lines": count_lines(filepath),
        }
        return data
    except Exception:
        return {}
