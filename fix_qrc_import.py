from pathlib import Path


def main() -> None:
    """Replace str 'import LobsterLogReporter_rc' with 'import gui.qrc.LobsterLogReporter_rc' in the file D:/GitHub/LobsterLogReporter/src/gui/ui/main/LobsterGeneralLogViewer_ui.py

    Returns:
        None: Nothing :)
    """

    PATH: str = r"src\gui\LobsterGeneralLogViewer_ui.py"

    TO_REPLACE_STR: str = "import LobsterLogReporter_rc"
    REPLACE_STR: str = "from gui.assets.qrc import LobsterLogReporter_rc"

    def read_file_lines(filepath: str) -> list[str]:
        path: Path = Path(filepath)

        with open(file=path, mode="r", encoding="UTF-8") as file:
            lines = file.readlines()

        return lines

    def replace_line(
        lines: list[str], to_replace_str=TO_REPLACE_STR, replace_str=REPLACE_STR
    ) -> list[str]:
        modified_lines = []
        for line in lines:
            if to_replace_str in line:
                line = line.replace(to_replace_str, replace_str)
                print(f"Replaced string '{to_replace_str}' with string '{replace_str}'")
            modified_lines.append(line)
        return modified_lines

    def write_file_lines(filepath: str, lines: list[str]) -> None:
        path: Path = Path(filepath)
        with open(file=path, mode="w", encoding="UTF-8") as file:
            file.writelines(lines)
        print(f"File saved: {filepath}")

    file_lines = read_file_lines(PATH)
    modified_lines = replace_line(file_lines)
    write_file_lines(PATH, modified_lines)


if __name__ == "__main__":
    main()
