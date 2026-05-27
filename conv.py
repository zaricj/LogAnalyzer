import pandas as pd
from pathlib import Path

def convert_csv_to_excel(input_csv_file: Path, output_excel_file: Path):
    if not input_csv_file.exists():
        raise FileNotFoundError("Invalid input file.")

    chunk_size = 1024

    # read_csv is significantly faster than the csv module for large files
    csv_reader = pd.read_csv(
        input_csv_file,
        sep=";",
        quotechar='"',
        encoding="utf-8",
        engine="c",
        chunksize=chunk_size,
    )

    # Using ExcelWriter to handle sequential writing
    print("Converting CSV to Excel now, please wait")
    with pd.ExcelWriter(output_excel_file, engine="xlsxwriter") as writer:
        for i, chunk in enumerate(csv_reader):
            write_header = i == 0
            start_row = i * chunk_size
            # to_excel handles all type conversions (ints, floats, strings) natively
            chunk.to_excel(
                writer,
                sheet_name="Result",
                startrow=start_row,
                index=False,
                header=write_header,
            )
            
    print("Excel conversion completed!")
    
file = r"C:\Users\ZaricJ\Documents\Entwicklung_und_Tools\GitHub\Glint\output\2026_05_26_http_requests_general.csv"

convert_csv_to_excel(Path(file), Path("Output.xlsx"))
