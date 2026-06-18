# ChaBiao 查表 - Fast Spreadsheet Viewer, Filter & Processor

⚡ Lightning-fast spreadsheet viewer, filter and processor. Built for large Excel files (15MB+, 20K+ rows) that make Excel choke on filter dropdowns.

## Features

- **Fast Filtering**: Instant column filtering - no more waiting for Excel's filter dropdown to load
- **Keyword Search**: Full-text search across all columns with regex support
- **Spotlight / Focus Cell**: Highlight active row and column for easy reading (聚光灯功能)
- **Cross-Reference**: Search in one table, extract columns to another (查表整合)
- **Multi-format**: Support .xlsx, .xls, .csv, .tsv, .xlsm, .ods
- **Three Interfaces**: CLI, PySide6 GUI, and Web (FastAPI)
- **Data Aggregation**: Pivot tables, group-by, subtotals
- **File Comparison**: Merge and compare two spreadsheet files
- **Export**: Convert between formats (xlsx, csv, json, tsv)
- **Agent Integration**: OpenAI function-calling tools for AI agents

## Requirements

- Python >= 3.10
- pandas >= 2.0
- openpyxl >= 3.1
- tabulate >= 0.9

Optional:
- PySide6 >= 6.5 (for GUI)
- FastAPI + uvicorn (for Web)

## Installation

```bash
# Basic (CLI only)
pip install chabiao

# With GUI support
pip install chabiao[gui]

# With Web support
pip install chabiao[web]

# Everything
pip install chabiao[all]

# Development
pip install chabiao[dev]
```

## Quick Start

### CLI

```bash
# Open and inspect a spreadsheet
chabiao open data.xlsx

# Filter by column with various conditions
chabiao filter data.xlsx --column City --contains Beijing
chabiao filter data.xlsx --column Price --gt 100 --lt 500
chabiao filter data.xlsx --column Sales --top-n 10

# Search for a keyword across columns
chabiao search data.xlsx --keyword error --columns Message,Level

# Aggregate data (like Excel pivot table)
chabiao aggregate data.xlsx --group-by City --agg Sales:sum --agg Price:mean

# Compare/merge two files
chabiao compare data1.xlsx data2.xlsx --on ID --how left

# Export to different format
chabiao export data.xlsx -o output.csv --format csv

# Spotlight on a specific row
chabiao spotlight data.xlsx --row 100 --column Price
```

### Python API

```python
from chabiao import open_file, filter_data, search_data, spotlight

# Open a spreadsheet
result = open_file(input_path="data.xlsx")
print(result.success)    # True
print(result.data)       # File info and metadata

# Filter data
result = filter_data(input_path="data.xlsx", column="City", contains="Beijing")
print(result.data["total_rows"])  # Number of matching rows

# Search across columns
result = search_data(input_path="data.xlsx", keyword="error", columns=["Message"])
print(result.data["total_matches"])

# Spotlight on a row
result = spotlight(input_path="data.xlsx", row=100, column="Price")
print(result.data["row_data"])       # Full row data
print(result.data["column_stats"])   # Column statistics
```

### GUI

```bash
chabiao-gui
# or
python -m chabiao --gui
```

Features:
- Drag & drop file opening
- Instant column filter dropdown (no lag!)
- Spotlight mode (F6) to highlight rows and columns
- Sheet tabs for multi-sheet workbooks
- Copy selection to clipboard (Ctrl+C)
- Export to CSV/JSON/Excel

### Web Interface

```bash
chabiao-web
# or
python -m chabiao --web
```

Open http://localhost:8900 in your browser.

## Usage

### CLI Unified Flags

| Flag | Description |
|------|-------------|
| `-V, --version` | Show version |
| `-v, --verbose` | Verbose output |
| `-o, --output` | Output file path |
| `--json` | Output as JSON |
| `-q, --quiet` | Suppress non-essential output |

### CLI Commands

| Command | Description |
|---------|-------------|
| `open` | Open and inspect a spreadsheet |
| `filter` | Filter data by column conditions |
| `search` | Search keyword across columns |
| `aggregate` | Aggregate data by grouping |
| `compare` | Compare/merge two spreadsheet files |
| `export` | Export data to different format |
| `spotlight` | Focus on a specific row/cell |

### Filter Options

| Option | Description |
|--------|-------------|
| `--contains` | Text contains filter |
| `--regex` | Regex pattern filter |
| `--equals` | Exact match filter |
| `--not-equals` | Not equal filter |
| `--gt` / `--lt` | Greater than / Less than |
| `--ge` / `--le` | Greater/Less than or equal |
| `--top-n` | Top N values |
| `--bottom-n` | Bottom N values |
| `--above-avg` | Above average |
| `--below-avg` | Below average |

## Agent Integration (OpenAI Function Calling)

```python
from chabiao.tools import TOOLS, dispatch

# Use TOOLS in your OpenAI API call
response = client.chat.completions.create(
    model="gpt-4",
    messages=[...],
    tools=TOOLS,
)

# Dispatch tool calls
for tool_call in response.choices[0].message.tool_calls:
    result = dispatch(tool_call.function.name, tool_call.function.arguments)
    print(result)
```

Available tools:
- `chabiao_open_file` - Open and inspect spreadsheet
- `chabiao_filter_data` - Filter with various conditions
- `chabiao_search_data` - Search keywords across columns
- `chabiao_aggregate_data` - Group and aggregate data
- `chabiao_compare_data` - Compare/merge two files
- `chabiao_export_data` - Export to different format
- `chabiao_spotlight` - Focus on a specific row/cell

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Lint and format
ruff format . && ruff check .

# Type check
mypy chabiao

# Build
python -m build
```

## License

GPL-3.0-or-later