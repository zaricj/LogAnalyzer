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
- **Progress Tracking**: Visual progress bars with `rich` progress indicators
- **Flexible Configuration**: JSON-based pattern definitions
- **Multiple Export Formats**: CSV export functionality
- **Console Interface**: Command-line interface for processing

## CLI Usage

Glint features a command-line interface powered by `typer` with two primary commands: `run` and `patterns`.

### 1. View Available Pattern Keys (`patterns`)

List all available search pattern keys configured in your JSON pattern file:

```bash
# List pattern keys using the default config file (patterns/patterns.json)
python main.py patterns

# Specify a custom config file
python main.py patterns --config path/to/custom_patterns.json
```

### 2. Run the Extraction Pipeline (`run`)

The `run` command executes log parsing and exports the extracted data to CSV/Excel.

> **Note:** Options `--pattern` (`-p`), `--dir` (`-d`), and `--output-dir` (`-o`) are **mandatory**.

#### Basic Run Command

```bash
python main.py run \
  --pattern lobster_log \
  --dir ./logs \
  --output-dir ./output
```

#### Full Run Command Options

```bash
python main.py run \
  --config patterns/patterns.json \
  --pattern catalina_out_jasperserver \
  --dir ./logs \
  --file-pattern "*.out" \
  --output-dir ./output \
  --keyword "SEVERE" \
  --progress
```

#### Command Options Reference (`run`)

| Option | Short | Type | Default | Required | Description |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `--pattern` | `-p` | `TEXT` | *None* | **Yes** | Pattern key to use for searching (use `patterns` to list available keys). |
| `--dir` | `-d` | `PATH` | *None* | **Yes** | Path to the directory containing log files to search. |
| `--output-dir` | `-o` | `PATH` | *None* | **Yes** | Directory where generated CSV/Excel reports will be saved. |
| `--config` | `-c` | `PATH` | `patterns/patterns.json` | No | Path to the patterns JSON configuration file. |
| `--file-pattern`| `-f` | `TEXT` | `*.log` | No | Glob pattern to match log files (e.g., `*.out`, `*.log`). |
| `--keyword` | `-k` | `TEXT` | `""` | No | Optional keyword filter to prune event blocks. |
| `--progress` / `--no-progress` | | `BOOL` | `True` | No | Show/hide interactive Rich progress bars during file processing. |

#### Getting CLI Help

Display usage details directly in your terminal:

```bash
# View general CLI help
python main.py --help

# View help for the run command
python main.py run --help

# View help for the patterns command
python main.py patterns --help
```

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
├── .git/                      # Version control
├── .gitignore                 # Git ignore rules
├── .python-version            # Python version specification
├── main.py                    # Main application entry point
├── src/                       # Source code root
│   └── modules/               # Core application modules
│       ├── __init__.py
│       ├── core/              # Core processing modules
│       │   ├── parser.py      # Pattern parsing and extraction
│       │   ├── pipeline.py    # Pipeline orchestration
│       │   ├── thread_executor.py # Parallel processing management
│       │   ├── timestamp.py   # Time formatting utilities
│       │   ├── ui.py          # Console UI components
│       │   └── utils.py       # Utility functions
│       └── io/                # I/O handling modules
│           ├── config.py      # Configuration management
│           ├── converters.py  # Format conversions
│           ├── exporters.py   # CSV export functionality
│           └── file_utils.py  # File utilities
├── patterns/
│   └── patterns.json         # Pattern definitions
├── pyproject.toml            # Project configuration and dependencies
├── uv.lock                   # Dependency lock file
└── README.md                 # Documentation
```

## Quick Start

### Installation

1. **Prerequisites**: Python 3.13+
2. **Create virtual environment**:
  ```bash
  python -m venv .venv
  ```
3. **Activate environment**:
  ```bash
  # Windows
  .venv\Scripts\Activate.ps1
  
  # Linux/Mac
  source .venv/bin/activate
  ```
4. **Install dependencies**:
  ```bash
  pip install -e .
  ```

### Running the Tool

```bash
# Run from project root
python main.py
```

## Usage Examples

### Basic Pattern Matching

```python
from src.modules.core.pipeline import run_pipeline

result = run_pipeline(
    patterns_config="patterns/patterns.json",
    pattern_key="http_requests_jasperserver",
    files_directory="logs/",
    file_pattern="*.log",
    output_csv="output/results.csv",
    event_keyword="",
    show_progress=True
)
```

### Processing Multiple Files

```bash
python main.py \
  --patterns patterns/patterns.json \
  --pattern http_requests_jasperserver \
  --files logs/*.log \
  --output output/report.csv \
  --progress
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

- `pandas` >= 3.0.2 - Data manipulation
- `rich` >= 15.0.0 - Console formatting and progress bars
- `xlsxwriter` >= 3.2.9 - Excel generation (optional)
- `typer` - CLI command runner and argument parsing

### Adding New Patterns

1. Edit `patterns/patterns.json`
2. Add a new pattern key
3. Define your regex patterns with multiple capture groups
4. Test in `main.py`

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

**Need help?** Check the source code in `main.py` or create an issue on the repository.