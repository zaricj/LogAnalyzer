from __future__ import annotations

from pathlib import Path

import pandas as pd


def export_to_csv(data: pd.DataFrame, save_as_path: str, delimiter: str = ";") -> str:
    output_path = Path(save_as_path)
    data.to_csv(output_path, sep=delimiter, index=False, encoding="utf-8")
    return str(output_path)


def export_to_excel(data: pd.DataFrame, save_as_path: str) -> str:
    output_path = Path(save_as_path)
    sheet_name = "Result"

    with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
        data.to_excel(writer, sheet_name=sheet_name, index=False)
        if not data.empty:
            worksheet = writer.sheets[sheet_name]
            max_row, max_col = data.shape
            column_settings = [{"header": col} for col in data.columns]
            worksheet.add_table(
                0,
                0,
                max_row,
                max_col - 1,
                {
                    "columns": column_settings,
                    "style": "Table Style Medium 16",
                    "name": sheet_name,
                    "autofilter": True,
                },
            )
            worksheet.set_column(0, max_col - 1, 22)

    return str(output_path)
