import csv
import xlsxwriter
from pathlib import Path
from typing import Iterator
from src.modules.core.ui import CONSOLE
from src.modules.io.file_utils import ensure_output_dir

# ========== CSV ==========


def write_csv(output: Path, headers: list[str], rows: Iterator[dict]) -> int:
    """Writes rows to a CSV file with the specified headers.

    Args:
        output (Path): The path to the output CSV file.
        headers (list[str]): A list of column headers for the CSV.
        rows (Iterator[dict]): An iterator over dictionaries representing each row.

    Returns:
        int: The number of rows written to the CSV file.
    """
    count = 0

    if not output.parent.exists():
        ensure_output_dir(output)

    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=headers, delimiter=";", quotechar='"', quoting=csv.QUOTE_ALL
        )
        writer.writeheader()

        for row in rows:
            normalized = {k: row.get(k, "") for k in headers}
            writer.writerow(normalized)
            count += 1

    return count


# ========== Excel Conversion ==========


def convert_csv_to_excel(input_csv_file: Path, output_excel_file: Path):
    if not input_csv_file.exists():
        raise FileNotFoundError("Invalid input file.")

    with CONSOLE.status("[bold]>>> Converting CSV to Excel...[/bold]", spinner="arc"):
        # constant_memory=True streams data straight to disk, keeping memory usage near zero.
        workbook_options = {
            "constant_memory": True,
            "default_date_format": "dd.mm.yyyy hh:mm:ss",
            "nan_inf_to_errors": True
        }

        with xlsxwriter.Workbook(str(output_excel_file), workbook_options) as workbook:
            worksheet = workbook.add_worksheet("Result")

            # Formats to optimize cell data writing
            int_format = workbook.add_format({"num_format": "#,##0"})
            float_format = workbook.add_format({"num_format": "#,##0.00"})

            with open(input_csv_file, "r", newline="", encoding="utf-8") as csvfile:
                # Use standard csv reader since it's incredibly light
                reader = csv.reader(csvfile, delimiter=";", quotechar='"')

                for row_idx, row in enumerate(reader):
                    for col_idx, cell in enumerate(row):
                        # Don't try to format the header row
                        if row_idx == 0:
                            worksheet.write(row_idx, col_idx, cell)
                            continue

                        # Optimistic type conversion for numeric fields
                        if not cell:
                            worksheet.write_blank(row_idx, col_idx, None)
                        elif cell.isdigit():
                            worksheet.write_number(
                                row_idx, col_idx, int(cell), int_format
                            )
                        else:
                            try:
                                # Fallback check for decimal values
                                float_val = float(cell)
                                worksheet.write_number(
                                    row_idx, col_idx, float_val, float_format
                                )
                            except ValueError:
                                # Standard fallback for strings (and your timestamp string)
                                worksheet.write_string(row_idx, col_idx, cell)
