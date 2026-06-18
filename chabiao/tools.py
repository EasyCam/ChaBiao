"""OpenAI function-calling tool definitions for ChaBiao."""

from __future__ import annotations

import json
from typing import Any

from .api import (
    aggregate_data,
    compare_data,
    export_data,
    filter_data,
    open_file,
    search_data,
)
from .api import (
    spotlight as spotlight_view,
)

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "chabiao_open_file",
            "description": "Open and inspect a spreadsheet file (.xlsx, .xls, .csv, etc.). Returns file metadata, sheet names, column info, and row counts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the spreadsheet file to open",
                    },
                    "sheet_name": {
                        "type": "string",
                        "description": "Specific sheet name to open. Defaults to first sheet.",
                    },
                },
                "required": ["input_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chabiao_filter_data",
            "description": "Filter data in a spreadsheet column with various conditions. Supports text contains, regex, exact match, numeric comparisons, top/bottom N, and above/below average filters.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the spreadsheet file",
                    },
                    "column": {
                        "type": "string",
                        "description": "Column name to filter on",
                    },
                    "contains": {
                        "type": "string",
                        "description": "Text contains filter",
                    },
                    "regex": {
                        "type": "string",
                        "description": "Regex pattern filter",
                    },
                    "equals": {
                        "description": "Exact match filter value",
                    },
                    "not_equals": {
                        "description": "Not equal filter value",
                    },
                    "greater_than": {
                        "type": "number",
                        "description": "Greater than numeric filter",
                    },
                    "less_than": {
                        "type": "number",
                        "description": "Less than numeric filter",
                    },
                    "greater_equal": {
                        "type": "number",
                        "description": "Greater than or equal filter",
                    },
                    "less_equal": {
                        "type": "number",
                        "description": "Less than or equal filter",
                    },
                    "top_n": {
                        "type": "integer",
                        "description": "Top N values filter",
                    },
                    "bottom_n": {
                        "type": "integer",
                        "description": "Bottom N values filter",
                    },
                    "above_avg": {
                        "type": "boolean",
                        "description": "Filter values above average",
                    },
                    "below_avg": {
                        "type": "boolean",
                        "description": "Filter values below average",
                    },
                    "sheet": {
                        "description": "Sheet name or index",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to save filtered results",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "csv", "xlsx", "tsv"],
                        "description": "Output format",
                    },
                },
                "required": ["input_path", "column"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chabiao_search_data",
            "description": "Search for a keyword across columns in a spreadsheet. Supports case-insensitive search and regex mode.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the spreadsheet file",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "Search keyword or pattern",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to search in. Null = all columns.",
                    },
                    "case_sensitive": {
                        "type": "boolean",
                        "description": "Case-sensitive search",
                    },
                    "regex_mode": {
                        "type": "boolean",
                        "description": "Treat keyword as regex pattern",
                    },
                    "sheet": {
                        "description": "Sheet name or index",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to save search results",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "csv", "xlsx", "tsv"],
                        "description": "Output format",
                    },
                },
                "required": ["input_path", "keyword"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chabiao_aggregate_data",
            "description": "Aggregate data by grouping columns (like Excel pivot/subtotal). Supports sum, mean, count, min, max, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the spreadsheet file",
                    },
                    "group_by": {
                        "description": "Column(s) to group by. String or list of strings.",
                    },
                    "aggregations": {
                        "type": "object",
                        "description": 'Dict mapping column name to aggregation function(s). E.g. {"Sales": "sum", "Price": ["mean", "max"]}',
                        "additionalProperties": {
                            "oneOf": [
                                {"type": "string"},
                                {"type": "array", "items": {"type": "string"}},
                            ]
                        },
                    },
                    "sheet": {
                        "description": "Sheet name or index",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to save aggregated results",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "csv", "xlsx", "tsv"],
                        "description": "Output format",
                    },
                },
                "required": ["input_path", "group_by", "aggregations"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chabiao_compare_data",
            "description": "Compare or merge two spreadsheet files by key columns. Supports inner, outer, left, right joins like SQL.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the primary spreadsheet file",
                    },
                    "other_path": {
                        "type": "string",
                        "description": "Path to the secondary spreadsheet file",
                    },
                    "on": {
                        "description": "Column(s) to merge on. String or list of strings.",
                    },
                    "how": {
                        "type": "string",
                        "enum": ["inner", "outer", "left", "right"],
                        "description": "Merge type",
                    },
                    "sheet": {
                        "description": "Sheet in primary file",
                    },
                    "other_sheet": {
                        "description": "Sheet in secondary file",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Optional path to save merged results",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["json", "csv", "xlsx", "tsv"],
                        "description": "Output format",
                    },
                },
                "required": ["input_path", "other_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chabiao_export_data",
            "description": "Export spreadsheet data to a different format (xlsx, csv, json, tsv) with optional column and row selection.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the source spreadsheet file",
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Path for the output file",
                    },
                    "output_format": {
                        "type": "string",
                        "enum": ["xlsx", "csv", "json", "tsv"],
                        "description": "Output format",
                    },
                    "sheet": {
                        "description": "Sheet name or index",
                    },
                    "columns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Columns to export. Null = all columns.",
                    },
                    "start_row": {
                        "type": "integer",
                        "description": "Start row index (0-based)",
                    },
                    "end_row": {
                        "type": "integer",
                        "description": "End row index (exclusive)",
                    },
                },
                "required": ["input_path", "output_path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "chabiao_spotlight",
            "description": "Focus on a specific row or cell with context, like Excel's spotlight/focus cell feature. Shows surrounding rows and column statistics.",
            "parameters": {
                "type": "object",
                "properties": {
                    "input_path": {
                        "type": "string",
                        "description": "Path to the spreadsheet file",
                    },
                    "row": {
                        "type": "integer",
                        "description": "Row index to focus on (0-based)",
                    },
                    "column": {
                        "type": "string",
                        "description": "Column name for cell-level spotlight. Optional.",
                    },
                    "sheet": {
                        "description": "Sheet name or index",
                    },
                },
                "required": ["input_path", "row"],
            },
        },
    },
]


def dispatch(name: str, arguments: dict[str, Any] | str) -> dict:
    """Dispatch tool call to appropriate API function."""
    if isinstance(arguments, str):
        arguments = json.loads(arguments)

    if name == "chabiao_open_file":
        result = open_file(**arguments)
    elif name == "chabiao_filter_data":
        result = filter_data(**arguments)
    elif name == "chabiao_search_data":
        result = search_data(**arguments)
    elif name == "chabiao_aggregate_data":
        result = aggregate_data(**arguments)
    elif name == "chabiao_compare_data":
        result = compare_data(**arguments)
    elif name == "chabiao_export_data":
        result = export_data(**arguments)
    elif name == "chabiao_spotlight":
        result = spotlight_view(**arguments)
    else:
        raise ValueError(f"Unknown tool: {name}")

    return result.to_dict()
