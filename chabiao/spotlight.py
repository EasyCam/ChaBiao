"""Spotlight / focus cell feature for ChaBiao - highlights active row and column."""

from __future__ import annotations

from typing import Any

import pandas as pd

from .core import SheetWorkbook


def spotlight(
    wb: SheetWorkbook,
    row: int,
    column: str | None = None,
    highlight_rows: int = 0,
    highlight_cols: list[str] | None = None,
    sheet: str | int | None = None,
) -> dict[str, Any]:
    """Get spotlight view: highlight the focused row and optionally column.

    Returns:
        Dict with 'focused_row', 'context_above', 'context_below',
        'row_data', 'column_stats' (if column specified).
    """
    df = wb.get_sheet(sheet)
    total_rows = len(df)

    if row < 0 or row >= total_rows:
        raise IndexError(f"Row index {row} out of range [0, {total_rows - 1}]")

    focused = df.iloc[row]

    above_start = max(0, row - 5 - highlight_rows)
    context_above = df.iloc[above_start:row]

    below_end = min(total_rows, row + 6 + highlight_rows)
    context_below = df.iloc[row + 1 : below_end]

    result: dict[str, Any] = {
        "row_index": row,
        "total_rows": total_rows,
        "row_data": focused.to_dict(),
        "context_above": context_above.to_dict(orient="records"),
        "context_below": context_below.to_dict(orient="records"),
    }

    if column and column in df.columns:
        col_data = df[column]
        result["column_stats"] = {
            "name": column,
            "dtype": str(col_data.dtype),
            "value_at_row": focused[column],
            "unique_count": int(col_data.nunique()),
            "null_count": int(col_data.isnull().sum()),
        }
        if pd.api.types.is_numeric_dtype(col_data):
            result["column_stats"]["mean"] = float(col_data.mean())
            result["column_stats"]["sum"] = float(col_data.sum())
            result["column_stats"]["min"] = float(col_data.min())
            result["column_stats"]["max"] = float(col_data.max())

    return result


def spotlight_range(
    wb: SheetWorkbook,
    start_row: int,
    end_row: int,
    columns: list[str] | None = None,
    sheet: str | int | None = None,
) -> dict[str, Any]:
    """Get a range of rows with spotlight focus, like selecting a range in Excel."""
    df = wb.get_sheet(sheet)
    total_rows = len(df)

    start_row = max(0, start_row)
    end_row = min(total_rows, end_row)

    subset = df.iloc[start_row:end_row]
    if columns:
        subset = subset[columns]

    return {
        "start_row": start_row,
        "end_row": end_row,
        "total_rows": total_rows,
        "columns": list(subset.columns),
        "row_count": len(subset),
        "data": subset.to_dict(orient="records"),
    }


def spotlight_cell(
    wb: SheetWorkbook,
    row: int,
    column: str,
    show_context: int = 3,
    sheet: str | int | None = None,
) -> dict[str, Any]:
    """Focus on a single cell with surrounding context - like Excel's cell spotlight."""
    df = wb.get_sheet(sheet)

    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found. Available: {list(df.columns)}")

    cell_value = df.at[df.index[row], column] if row < len(df) else None

    col_series = df[column]

    row_start = max(0, row - show_context)
    row_end = min(len(df), row + show_context + 1)
    context_rows = df.iloc[row_start:row_end][[column]].to_dict(orient="records")

    result: dict[str, Any] = {
        "cell": {"row": row, "column": column, "value": cell_value},
        "row_context": context_rows,
        "column_info": {
            "dtype": str(col_series.dtype),
            "unique_count": int(col_series.nunique()),
        },
    }

    if pd.api.types.is_numeric_dtype(col_series):
        result["column_info"].update(
            {
                "mean": float(col_series.mean()),
                "sum": float(col_series.sum()),
                "min": float(col_series.min()),
                "max": float(col_series.max()),
            }
        )
        result["column_info"]["count_above"] = (
            int((col_series > cell_value).sum()) if pd.notna(cell_value) else 0
        )
        result["column_info"]["count_below"] = (
            int((col_series < cell_value).sum()) if pd.notna(cell_value) else 0
        )

    return result


def cross_reference(
    wb: SheetWorkbook,
    keyword: str,
    source_columns: list[str],
    target_columns: list[str] | None = None,
    case_sensitive: bool = False,
    sheet: str | int | None = None,
) -> dict[str, Any]:
    """Find a keyword across source columns, then extract target columns.

    This mimics the common Excel workflow of:
    1. Search/filter in one area
    2. Copy relevant data to another area
    """
    from .filters import search_keyword

    matches = search_keyword(
        wb,
        keyword,
        columns=source_columns,
        case_sensitive=case_sensitive,
        sheet=sheet,
    )

    if target_columns:
        available = [c for c in target_columns if c in matches.columns]
        if available:
            result_df = matches[available]
        else:
            result_df = matches[source_columns]
    else:
        result_df = matches

    return {
        "keyword": keyword,
        "total_matches": len(result_df),
        "columns": list(result_df.columns),
        "data": result_df.to_dict(orient="records"),
    }
