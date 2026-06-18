"""Unified Python API for ChaBiao with ToolResult pattern."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from .__version__ import __version__
from .core import SheetWorkbook, load_workbook


@dataclass
class ToolResult:
    success: bool
    data: Any = None
    error: str | None = None
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
        }


def _serialize_df(df: pd.DataFrame) -> list[dict]:
    return df.to_dict(orient="records")


def _wb_info(wb: SheetWorkbook) -> dict:
    return {
        "path": str(wb.path),
        "format": wb.format,
        "sheet_names": wb.sheet_names,
        "active_sheet": wb.active_sheet,
        "shape": wb.shape(),
        "version": __version__,
    }


def open_file(
    *,
    input_path: str,
    sheet_name: str | int | None = None,
) -> ToolResult:
    """Open a spreadsheet file for viewing and analysis.

    Args:
        input_path: Path to the spreadsheet file (.xlsx, .xls, .csv, etc.)
        sheet_name: Specific sheet name or index to open. Default opens first sheet.

    Returns:
        ToolResult with file info and sheet metadata.
    """
    try:
        wb = load_workbook(input_path, sheet_name=sheet_name)
        info = wb.info_dict()
        return ToolResult(
            success=True,
            data={**_wb_info(wb), "info": info},
            metadata={"version": __version__},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def filter_data(
    *,
    input_path: str,
    column: str,
    sheet: str | int | None = None,
    contains: str | None = None,
    regex: str | None = None,
    equals: Any | None = None,
    not_equals: Any | None = None,
    greater_than: float | None = None,
    less_than: float | None = None,
    greater_equal: float | None = None,
    less_equal: float | None = None,
    between: tuple[float, float] | None = None,
    values: list[Any] | None = None,
    startswith: str | None = None,
    endswith: str | None = None,
    is_null: bool = False,
    not_null: bool = False,
    top_n: int | None = None,
    bottom_n: int | None = None,
    above_avg: bool = False,
    below_avg: bool = False,
    output_path: str | None = None,
    output_format: str = "json",
) -> ToolResult:
    """Filter data in a spreadsheet column with various conditions.

    Args:
        input_path: Path to the spreadsheet file.
        column: Column name to filter on.
        sheet: Sheet name or index.
        contains: Text contains filter.
        regex: Regex pattern filter.
        equals: Exact match filter.
        not_equals: Not equal filter.
        greater_than: Greater than numeric filter.
        less_than: Less than numeric filter.
        greater_equal: Greater than or equal filter.
        less_equal: Less than or equal filter.
        between: Tuple of (min, max) for range filter.
        values: List of values for IN filter.
        startswith: Text starts with filter.
        endswith: Text ends with filter.
        is_null: Filter for null values.
        not_null: Filter for non-null values.
        top_n: Top N values filter.
        bottom_n: Bottom N values filter.
        above_avg: Filter values above average.
        below_avg: Filter values below average.
        output_path: Optional path to save filtered results.
        output_format: Output format (json, csv, xlsx).

    Returns:
        ToolResult with filtered data.
    """
    from .filters import auto_filter, filter_column

    try:
        wb = load_workbook(input_path, sheet_name=sheet)

        if top_n is not None or bottom_n is not None or above_avg or below_avg:
            result_df = auto_filter(
                wb,
                column,
                top_n=top_n,
                bottom_n=bottom_n,
                above_avg=above_avg,
                below_avg=below_avg,
                sheet=sheet,
            )
        else:
            result_df = filter_column(
                wb,
                column,
                values=values,
                contains=contains,
                regex=regex,
                equals=equals,
                not_equals=not_equals,
                greater_than=greater_than,
                less_than=less_than,
                greater_equal=greater_equal,
                less_equal=less_equal,
                between=between,
                is_null=is_null,
                not_null=not_null,
                startswith=startswith,
                endswith=endswith,
                sheet=sheet,
            )

        data = _serialize_df(result_df)

        if output_path:
            _save_result(result_df, output_path, output_format)

        return ToolResult(
            success=True,
            data={
                "total_rows": len(result_df),
                "columns": list(result_df.columns),
                "rows": data,
            },
            metadata={"version": __version__, "source": str(wb.path)},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def search_data(
    *,
    input_path: str,
    keyword: str,
    columns: list[str] | None = None,
    case_sensitive: bool = False,
    regex_mode: bool = False,
    sheet: str | int | None = None,
    output_path: str | None = None,
    output_format: str = "json",
) -> ToolResult:
    """Search for a keyword across columns in a spreadsheet.

    Args:
        input_path: Path to the spreadsheet file.
        keyword: Search keyword or pattern.
        columns: List of columns to search in. None = all columns.
        case_sensitive: Case-sensitive search.
        regex_mode: Treat keyword as regex pattern.
        sheet: Sheet name or index.
        output_path: Optional path to save search results.
        output_format: Output format (json, csv, xlsx).

    Returns:
        ToolResult with matching rows.
    """
    from .filters import search_keyword

    try:
        wb = load_workbook(input_path, sheet_name=sheet)
        result_df = search_keyword(
            wb,
            keyword,
            columns=columns,
            case_sensitive=case_sensitive,
            regex_mode=regex_mode,
            sheet=sheet,
        )
        data = _serialize_df(result_df)

        if output_path:
            _save_result(result_df, output_path, output_format)

        return ToolResult(
            success=True,
            data={
                "keyword": keyword,
                "total_matches": len(result_df),
                "columns": list(result_df.columns),
                "rows": data,
            },
            metadata={"version": __version__},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def aggregate_data(
    *,
    input_path: str,
    group_by: str | list[str],
    aggregations: dict[str, str | list[str]],
    sheet: str | int | None = None,
    output_path: str | None = None,
    output_format: str = "json",
) -> ToolResult:
    """Aggregate data by grouping columns (like Excel pivot/subtotal).

    Args:
        input_path: Path to the spreadsheet file.
        group_by: Column(s) to group by.
        aggregations: Dict mapping column -> aggregation function(s).
        sheet: Sheet name or index.
        output_path: Optional path to save aggregated results.
        output_format: Output format (json, csv, xlsx).

    Returns:
        ToolResult with aggregated data.
    """
    from .filters import group_aggregate

    try:
        wb = load_workbook(input_path, sheet_name=sheet)
        result_df = group_aggregate(wb, group_by=group_by, agg_dict=aggregations, sheet=sheet)
        data = _serialize_df(result_df)

        if output_path:
            _save_result(result_df, output_path, output_format)

        return ToolResult(
            success=True,
            data={
                "total_groups": len(result_df),
                "columns": list(result_df.columns),
                "rows": data,
            },
            metadata={"version": __version__},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def compare_data(
    *,
    input_path: str,
    other_path: str,
    on: str | list[str] | None = None,
    how: str = "inner",
    sheet: str | int | None = None,
    other_sheet: str | int | None = None,
    output_path: str | None = None,
    output_format: str = "json",
) -> ToolResult:
    """Compare/merge two spreadsheet files by key columns.

    Args:
        input_path: Path to the primary spreadsheet file.
        other_path: Path to the secondary spreadsheet file.
        on: Column(s) to merge on. None = concat vertically.
        how: Merge type: inner, outer, left, right.
        sheet: Sheet in primary file.
        other_sheet: Sheet in secondary file.
        output_path: Optional path to save merged results.
        output_format: Output format (json, csv, xlsx).

    Returns:
        ToolResult with merged data.
    """
    try:
        wb1 = load_workbook(input_path, sheet_name=sheet)
        df1 = wb1.active_df
        wb2 = load_workbook(other_path, sheet_name=other_sheet)
        df2 = wb2.active_df

        if on:
            result_df = df1.merge(df2, on=on, how=how)
        else:
            result_df = pd.concat([df1, df2], ignore_index=True)

        data = _serialize_df(result_df)

        if output_path:
            _save_result(result_df, output_path, output_format)

        return ToolResult(
            success=True,
            data={
                "total_rows": len(result_df),
                "columns": list(result_df.columns),
                "source1_rows": len(df1),
                "source2_rows": len(df2),
                "rows": data,
            },
            metadata={"version": __version__},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def export_data(
    *,
    input_path: str,
    output_path: str,
    output_format: str = "xlsx",
    sheet: str | int | None = None,
    columns: list[str] | None = None,
    start_row: int = 0,
    end_row: int | None = None,
) -> ToolResult:
    """Export spreadsheet data to a different format or with selected columns/rows.

    Args:
        input_path: Path to the source spreadsheet file.
        output_path: Path for the output file.
        output_format: Output format (xlsx, csv, json, tsv).
        sheet: Sheet name or index.
        columns: Optional list of columns to export.
        start_row: Start row index (0-based).
        end_row: End row index (exclusive).

    Returns:
        ToolResult with export info.
    """
    try:
        wb = load_workbook(input_path, sheet_name=sheet)
        df = wb.get_sheet(sheet)

        if columns:
            df = df[columns]
        if end_row is not None or start_row > 0:
            df = df.iloc[start_row:end_row]

        out = Path(output_path)
        _save_result(df, str(out), output_format)

        return ToolResult(
            success=True,
            data={
                "output_path": str(out),
                "format": output_format,
                "rows_exported": len(df),
                "columns_exported": list(df.columns),
            },
            metadata={"version": __version__},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def spotlight(
    *,
    input_path: str,
    row: int,
    column: str | None = None,
    sheet: str | int | None = None,
) -> ToolResult:
    """Focus on a specific row with context, like Excel's spotlight/focus cell feature.

    Args:
        input_path: Path to the spreadsheet file.
        row: Row index to focus on (0-based).
        column: Optional column name for cell-level spotlight.
        sheet: Sheet name or index.

    Returns:
        ToolResult with spotlight data.
    """
    from .spotlight import spotlight as _spotlight
    from .spotlight import spotlight_cell

    try:
        wb = load_workbook(input_path, sheet_name=sheet)

        if column:
            result = spotlight_cell(wb, row, column, sheet=sheet)
        else:
            result = _spotlight(wb, row, sheet=sheet)

        return ToolResult(
            success=True,
            data=result,
            metadata={"version": __version__},
        )
    except Exception as e:
        return ToolResult(success=False, error=str(e))


def _save_result(df: pd.DataFrame, output_path: str, output_format: str) -> Path:
    out = Path(output_path)
    fmt = output_format.lower()

    if fmt == "csv":
        df.to_csv(out, index=False)
    elif fmt == "xlsx":
        df.to_excel(out, index=False)
    elif fmt == "json":
        json_data = df.to_json(orient="records", force_ascii=False)
        out.write_text(json_data, encoding="utf-8")
    elif fmt == "tsv":
        df.to_csv(out, index=False, sep="\t")
    else:
        raise ValueError(f"Unsupported output format: {fmt}")

    return out
