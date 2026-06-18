"""CLI interface for ChaBiao - fast spreadsheet viewer, filter and processor."""

from __future__ import annotations

import argparse
import json
import logging
import sys

from .__version__ import __version__
from .api import (
    ToolResult,
    aggregate_data,
    compare_data,
    export_data,
    filter_data,
    open_file,
    search_data,
    spotlight,
)


def _print_result(result: ToolResult, json_output: bool = False, quiet: bool = False) -> None:
    if json_output:
        print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2, default=str))
    elif not quiet:
        if result.success:
            data = result.data
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == "rows":
                        import pandas as pd
                        from tabulate import tabulate

                        if value:
                            df = pd.DataFrame(value)
                            print(tabulate(df, headers="keys", tablefmt="grid", showindex=False))
                            print(f"\nTotal: {len(value)} rows")
                    elif isinstance(value, (list, dict)):
                        print(f"{key}: {json.dumps(value, ensure_ascii=False, default=str)[:200]}")
                    else:
                        print(f"{key}: {value}")
            else:
                print(data)
        else:
            print(f"Error: {result.error}", file=sys.stderr)


def _cmd_open(args: argparse.Namespace) -> None:
    result = open_file(input_path=args.input, sheet_name=args.sheet)
    _print_result(result, json_output=args.json_output, quiet=args.quiet)


def _cmd_filter(args: argparse.Namespace) -> None:
    result = filter_data(
        input_path=args.input,
        column=args.column,
        sheet=args.sheet,
        contains=args.contains,
        regex=args.regex,
        equals=args.equals,
        not_equals=args.not_equals,
        greater_than=args.gt,
        less_than=args.lt,
        greater_equal=args.ge,
        less_equal=args.le,
        top_n=args.top_n,
        bottom_n=args.bottom_n,
        above_avg=args.above_avg,
        below_avg=args.below_avg,
        output_path=args.output,
        output_format=args.format,
    )
    _print_result(result, json_output=args.json_output, quiet=args.quiet)


def _cmd_search(args: argparse.Namespace) -> None:
    result = search_data(
        input_path=args.input,
        keyword=args.keyword,
        columns=args.columns,
        case_sensitive=args.case_sensitive,
        regex_mode=args.regex,
        sheet=args.sheet,
        output_path=args.output,
        output_format=args.format,
    )
    _print_result(result, json_output=args.json_output, quiet=args.quiet)


def _cmd_aggregate(args: argparse.Namespace) -> None:
    aggregations = {}
    for agg in args.agg:
        col, func = agg.split(":", 1)
        aggregations[col] = func

    group_by = args.group_by if len(args.group_by) > 1 else args.group_by[0]

    result = aggregate_data(
        input_path=args.input,
        group_by=group_by,
        aggregations=aggregations,
        sheet=args.sheet,
        output_path=args.output,
        output_format=args.format,
    )
    _print_result(result, json_output=args.json_output, quiet=args.quiet)


def _cmd_compare(args: argparse.Namespace) -> None:
    on = args.on if args.on else None
    if on and len(on) == 1:
        on = on[0]

    result = compare_data(
        input_path=args.input,
        other_path=args.other,
        on=on,
        how=args.how,
        sheet=args.sheet,
        other_sheet=args.other_sheet,
        output_path=args.output,
        output_format=args.format,
    )
    _print_result(result, json_output=args.json_output, quiet=args.quiet)


def _cmd_export(args: argparse.Namespace) -> None:
    result = export_data(
        input_path=args.input,
        output_path=args.output,
        output_format=args.format,
        sheet=args.sheet,
        columns=args.columns,
        start_row=args.start_row,
        end_row=args.end_row,
    )
    _print_result(result, json_output=args.json_output, quiet=args.quiet)


def _cmd_spotlight(args: argparse.Namespace) -> None:
    result = spotlight(
        input_path=args.input,
        row=args.row,
        column=args.column,
        sheet=args.sheet,
    )
    _print_result(result, json_output=args.json_output, quiet=args.quiet)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chabiao",
        description=(
            "ChaBiao - Fast spreadsheet viewer, filter and processor / "
            "查表 - 闪电般的表格查阅筛选工具"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  chabiao open data.xlsx\n"
            "  chabiao filter data.xlsx --column City --contains Beijing\n"
            "  chabiao search data.xlsx --keyword error --columns Message,Level\n"
            "  chabiao aggregate data.xlsx --group-by City --agg Sales:sum\n"
            "  chabiao compare data1.xlsx data2.xlsx --on ID --how left\n"
            "  chabiao export data.xlsx -o output.csv --format csv\n"
            "  chabiao spotlight data.xlsx --row 100 --column Price\n"
        ),
    )

    parser.add_argument("-V", "--version", action="version", version=f"chabiao {__version__}")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-o", "--output", help="Output file path")
    parser.add_argument("--json", action="store_true", dest="json_output", help="Output as JSON")
    parser.add_argument("-q", "--quiet", action="store_true", help="Suppress non-essential output")

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # open
    p_open = subparsers.add_parser("open", help="Open and inspect a spreadsheet file")
    p_open.add_argument("input", help="Path to spreadsheet file")
    p_open.add_argument("--sheet", help="Sheet name or index")

    # filter
    p_filter = subparsers.add_parser("filter", help="Filter data by column conditions")
    p_filter.add_argument("input", help="Path to spreadsheet file")
    p_filter.add_argument("--column", required=True, help="Column to filter on")
    p_filter.add_argument("--sheet", help="Sheet name or index")
    p_filter.add_argument("--contains", help="Text contains filter")
    p_filter.add_argument("--regex", help="Regex pattern filter")
    p_filter.add_argument("--equals", help="Exact match filter")
    p_filter.add_argument("--not-equals", dest="not_equals", help="Not equal filter")
    p_filter.add_argument("--gt", type=float, help="Greater than")
    p_filter.add_argument("--lt", type=float, help="Less than")
    p_filter.add_argument("--ge", type=float, help="Greater than or equal")
    p_filter.add_argument("--le", type=float, help="Less than or equal")
    p_filter.add_argument("--top-n", type=int, help="Top N values")
    p_filter.add_argument("--bottom-n", type=int, help="Bottom N values")
    p_filter.add_argument("--above-avg", action="store_true", help="Above average")
    p_filter.add_argument("--below-avg", action="store_true", help="Below average")
    fmt_choices = ["json", "csv", "xlsx", "tsv"]
    p_filter.add_argument("--format", default="json", choices=fmt_choices, help="Output format")

    # search
    p_search = subparsers.add_parser("search", help="Search keyword across columns")
    p_search.add_argument("input", help="Path to spreadsheet file")
    p_search.add_argument("--keyword", "-k", required=True, help="Search keyword")
    p_search.add_argument("--columns", nargs="+", help="Columns to search in")
    p_search.add_argument("--case-sensitive", action="store_true", help="Case-sensitive search")
    p_search.add_argument("--regex", action="store_true", help="Regex mode")
    p_search.add_argument("--sheet", help="Sheet name or index")
    p_search.add_argument("--format", default="json", choices=fmt_choices, help="Output format")

    # aggregate
    p_agg = subparsers.add_parser("aggregate", help="Aggregate data by grouping")
    p_agg.add_argument("input", help="Path to spreadsheet file")
    p_agg.add_argument("--group-by", nargs="+", required=True, help="Column(s) to group by")
    p_agg.add_argument(
        "--agg",
        action="append",
        required=True,
        help="Aggregation: Column:func (e.g. Sales:sum)",
    )
    p_agg.add_argument("--sheet", help="Sheet name or index")
    p_agg.add_argument("--format", default="json", choices=fmt_choices, help="Output format")

    # compare
    p_compare = subparsers.add_parser("compare", help="Compare/merge two spreadsheet files")
    p_compare.add_argument("input", help="Path to primary spreadsheet file")
    p_compare.add_argument("other", help="Path to secondary spreadsheet file")
    p_compare.add_argument("--on", nargs="+", help="Column(s) to merge on")
    p_compare.add_argument(
        "--how",
        default="inner",
        choices=["inner", "outer", "left", "right"],
        help="Merge type",
    )
    p_compare.add_argument("--sheet", help="Sheet in primary file")
    p_compare.add_argument("--other-sheet", dest="other_sheet", help="Sheet in secondary file")
    p_compare.add_argument("--format", default="json", choices=fmt_choices, help="Output format")

    # export
    p_export = subparsers.add_parser("export", help="Export data to different format")
    p_export.add_argument("input", help="Path to spreadsheet file")
    p_export.add_argument("-o", "--output", required=True, help="Output file path")
    xlsx_choices = ["xlsx", "csv", "json", "tsv"]
    p_export.add_argument(
        "--format",
        default="xlsx",
        choices=xlsx_choices,
        help="Output format",
    )
    p_export.add_argument("--sheet", help="Sheet name or index")
    p_export.add_argument("--columns", nargs="+", help="Columns to export")
    p_export.add_argument("--start-row", type=int, default=0, help="Start row (0-based)")
    p_export.add_argument("--end-row", type=int, help="End row (exclusive)")

    # spotlight
    p_spot = subparsers.add_parser("spotlight", help="Focus on a specific row/cell")
    p_spot.add_argument("input", help="Path to spreadsheet file")
    p_spot.add_argument("--row", type=int, required=True, help="Row index (0-based)")
    p_spot.add_argument("--column", help="Column name for cell-level focus")
    p_spot.add_argument("--sheet", help="Sheet name or index")

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif args.quiet:
        logging.getLogger().setLevel(logging.WARNING)

    if not args.command:
        parser.print_help()
        sys.exit(0)

    commands = {
        "open": _cmd_open,
        "filter": _cmd_filter,
        "search": _cmd_search,
        "aggregate": _cmd_aggregate,
        "compare": _cmd_compare,
        "export": _cmd_export,
        "spotlight": _cmd_spotlight,
    }

    cmd_func = commands.get(args.command)
    if cmd_func:
        cmd_func(args)
    else:
        parser.print_help()
        sys.exit(1)
