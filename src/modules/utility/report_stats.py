from src.modules.core.timestamp import _MONTH_MAP
import pandas as pd

def generate_report(file_path, column_name):
    # Load data (assuming semicolon separator based on your file)
    df = pd.read_csv(file_path, sep=';')
    
    if column_name not in df.columns:
        return f"Error: Header '{column_name}' not found in file."

    series = df[column_name].copy()

    # 1. Try Numeric Calculation
    # This handles 'size', 'status', or actual duration numbers
    numeric_series = pd.to_numeric(series, errors='coerce')
    if numeric_series.notna().sum() > (len(series) * 0.5):  # If majority is numeric
        return {
            'Report Type': 'Numeric Values',
            'Average': numeric_series.mean(),
            'Max': numeric_series.max(),
            'Min': numeric_series.min()
        }

    # 2. Try Datetime Calculation
    # Handles timestamps by calculating the intervals (runtimes) between events
    if series.dtype == 'object':
        for key, value in _MONTH_MAP.items():
            if value in series.str:
                series = series.str.replace(value, key, regex=False)
    
    # Try general parsing first, then fallback to specific log format
    dt_series = pd.to_datetime(series, errors='coerce')
    if dt_series.isna().all():
        dt_series = pd.to_datetime(series, format='%d/%b/%Y:%H:%M:%S', errors='coerce')

    if dt_series.notna().sum() > 0:
        # Calculate time difference between sorted timestamps in seconds
        intervals = dt_series.sort_values().diff().dt.total_seconds()
        return {
            'Report Type': 'Time Intervals (Seconds)',
            'Average': intervals.mean(),
            'Max': intervals.max(),
            'Min': intervals.min()
        }

    return "Result: The column contains text/categories that cannot be averaged."

# --- Usage Example ---
if __name__ == "__main__":
    file_name = r"C:\Users\ZaricJ\Downloads\2026_05_13_http_requests_general.csv"
    target_header = "timestamp"
    
    report = generate_report(file_name, target_header)
    
    if isinstance(report, dict):
        print(f"\n--- {target_header} Report ({report['Report Type']}) ---")
        print(f"Average: {report['Average']:.2f}")
        print(f"Maximum: {report['Max']:.2f}")
        print(f"Minimum: {report['Min']:.2f}")
    else:
        print(report)