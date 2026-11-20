# Glint ✨

A powerful file analysis and pattern extraction tool designed to search through log files, extract structured information using regex patterns, and generate comprehensive reports.

## What It Does

Glint helps you:

- **Search and parse** various types of log files (application logs, SQL, FTP, HTTP, etc.)
- **Extract specific patterns** from log entries using regex-based definitions
- **Structure and organize** unstructured log data into actionable reports
- **Export results** to CSV for further analysis in spreadsheets
- **Process multiple files** concurrently with parallel threading

## Key Features

- **Pattern-Based Extraction**: Define regex patterns for different log formats
- **Event Block Extraction**: Identify and extract complete event blocks from logs
- **Multi-Pattern Support**: Match multiple patterns within a single event
- **Threading & Performance**: Parallel file processing with `ThreadPoolExecutor`
- **Live Progress**: Progress, matched rows and elapsed time shown live in the GUI
- **Flexible Configuration**: JSON-based pattern definitions
- **Multiple Export Formats**: CSV and Excel (.xlsx) export
- **Desktop GUI**: Modern PySide6 interface with automatic light/dark theme

## Usage

Glint is a PySide6 desktop application:

```bash
uv run app.py
```

Pick the patterns config, pattern key, log directory, file pattern, optional keyword and
output directory in the sidebar, then click **Run search** (or press `Ctrl+Enter`). The search
runs in a background thread with live progress, a streamed results preview (first 1,000 rows)
and an activity log. Press `Esc` to cancel at any time; the last used settings are remembered.
The theme button next to the logo cycles **System → Light → Dark** (System follows the OS
light/dark setting); the choice is remembered. The app icon lives in `assets/` — edit
`glint.svg` and run `uv run assets/make_icons.py` to regenerate `glint.png`/`glint.ico`.

The GUI follows MVVM:

| Layer | Location | Responsibility |
|---|---|---|
| Model | `src/models/` | `SearchConfig`/`SearchResult` dataclasses, GUI-agnostic `PipelineEngine` (callbacks + cancellation) |
| ViewModel | `src/viewmodels/` | `MainViewModel` state/commands, `SearchWorker` (`QThread`), `ResultsTableModel` |
| View | `src/views/` | `MainWindow` layout and bindings, `theme.py` design tokens/QSS, `widgets.py` custom widgets |

---

## Supported Log Formats

- SQL exceptions and errors
- Database pool size exceeded events
- FTP per-profile job logs
- HTTP requests (Jasperserver)
- Catalina output (Jasperserver)
- Custom patterns via JSON configuration

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Glint                                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────┐                                              │
│  │  Core Modules  │  → Pipeline orchestration                    │
│  │  ┌─────────┐   │                                              │
│  │  │ parser  │   │  → Event extraction & pattern matching       │
│  │  └─────────┘   │                                              │
│  │  ┌──────────┐  │                                              │
│  │  │ pipeline │  │  → File processing                           │
│  │  └──────────┘  │                                              │
│  │  ┌──────────┐  │                                              │
│  │  │ thread   │  │  → Parallel processing                       │
│  │  └──────────┘  │                                              │
│  │  ┌──────────┐  │                                              │
│  │  │ timestamp│  │  → Time formatting                           │
│  │  └──────────┘  │                                              │
│  │  ┌──────────┐  │                                              │
│  │  │ utils    │  │  → Utility functions                         │
│  │  └──────────┘  │                                              │
│  └────────────────┘                                              │
│                                                                  │
│  ┌──────────────────┐                                            │
│  │   I/O Modules    │  → File operations & exports               │
│  │  ┌───────────┐   │                                            │
│  │  │ config    │   │  → Configuration management                │
│  │  └───────────┘   │                                            │
│  │  ┌────────────┐  │                                            │
│  │  │ converters │  │  → Format conversions                      │
│  │  └────────────┘  │                                            │
│  │  ┌───────────┐   │                                            │
│  │  │ exporters │   │  → CSV generation                          │
│  │  └───────────┘   │                                            │
│  │  ┌────────────┐  │                                            │
│  │  │ file_utils │  │  → File utilities                          │
│  │  └────────────┘  │                                            │
│  └──────────────────┘                                            │
│                                                                  │
│  ┌────────────────┐                                              │
│  │ Configuration  │                                              │
│  │  ┌──────────┐  │                                              │
│  │  │ patterns │  │ → Pattern definitions                        │
│  │  └──────────┘  │                                              │
│  └────────────────┘                                              │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

## Project Structure

``` text
├── app.py                     # GUI entry point
├── benchmark/
│   └── main-profiling.py      # Headless cProfile run of the pipeline
├── patterns/
│   └── patterns.json          # Pattern definitions
├── src/
│   ├── models/                # SearchConfig, SearchResult, PipelineEngine
│   ├── viewmodels/            # MainViewModel, SearchWorker, ResultsTableModel
│   ├── views/                 # MainWindow, theme, custom widgets
│   └── modules/
│       ├── core/              # parser, timestamp
│       ├── io/                # exporters, converters, file_utils, regex_service
│       └── utility/           # thread_executor, report_stats
├── pyproject.toml
└── uv.lock
```

## Quick Start

1. **Prerequisites**: Python 3.14+ and [uv](https://docs.astral.sh/uv/)
2. **Install dependencies**: `uv sync`
3. **Run**: `uv run app.py`

### Scripting the pipeline

The pipeline engine has no Qt dependency and can be used headlessly:

```python
from pathlib import Path
from src.models import PipelineEngine, SearchConfig

result = PipelineEngine().run(SearchConfig(
    patterns_config=Path("patterns/patterns.json"),
    pattern_key="http_requests_jasperserver",
    files_directory=Path("logs"),
    file_pattern="*.log",
    output_directory=Path("output"),
))
print(result.status, result.rows_written, result.csv_path)
```

## Configuration

### Pattern Definitions

Edit `patterns/patterns.json` to define your extraction patterns:

```json
{
  "http_requests_jasperserver": {
    "base": {
      "separator": "^(?P<time>\\d{2}:\\d{2}:\\d{2})"
    },
    "patterns": {
      "http_request": ".*"
    }
  },
  "sql_exceptions": { ... },
  "db_pool_size_exceeded": { ... },
  "ftp_per_profile": { ... }
}
```

### Available Pattern Keys

| Key | Description |
|-----|-------------|
| `sql_exceptions` | Extract SQL query, error details, stack trace |
| `db_pool_size_exceeded` | Extract database pool connection info |
| `ftp_per_profile` | Extract FTP job information |
| `http_requests_jasperserver` | Extract HTTP request logs |
| `catalina_out_jasperserver` | Extract Catalina output logs |
| *(custom)* | Define your own patterns |

## Output Formats

### CSV Export

Results are exported to CSV files with columns:
- Timestamp
- Pattern matched
- Extracted data
- File source
- Additional fields

## Development

### Dependencies

- `pyside6-essentials` >= 6.12.0 - Desktop GUI
- `pandas` >= 3.1.0 - Data manipulation
- `xlsxwriter` >= 3.3.1 - Excel generation

### Adding New Patterns

1. Edit `patterns/patterns.json`
2. Add a new pattern key
3. Define your regex patterns with multiple capture groups
4. Reload the config in the GUI (refresh button next to the pattern key) and run a search

### JSON Configuration Structure

Every pattern key in `patterns.json` must contain a regex with multiple groups that will be used to search in an event block in a log file. This ensures that a single line contains all the matches from the same event block.

**Expected JSON structure**:
```json
{
    "category_name": {
        "base": {
            "separator": "regex_string"
        },
        "patterns": {
            "pattern_name": "regex_string",
            ...
        }
    },
    ...
}
```

## Contributing

To contribute:
1. Fork the repository
2. Create a feature branch
3. Add tests for new features
4. Submit a pull request

## License

MIT License - Feel free to use and modify!

## Author

Jovan

---

**Need help?** Check the source code in `src/` or create an issue on the repository.