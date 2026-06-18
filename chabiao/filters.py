"""Advanced filtering engine for ChaBiao - fast column filtering and search."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from .core import SheetWorkbook


def filter_column(
    wb: SheetWorkbook,
    column: str,
    values: list[Any] | None = None,
    contains: str | None = None,
    regex: str | None = None,
    equals: Any | None = None,
    not_equals: Any | None = None,
    greater_than: float | None = None,
    less_than: float | None = None,
    greater_equal: float | None = None,
    less_equal: float | None = None,
    between: tuple[float, float] | None = None,
    is_null: bool = False,
    not_null: bool = False,
    startswith: str | None = None,
    endswith: str | None = None,
    sheet: str | int | None = None,
) -> pd.DataFrame:
    """Filter a single column with various conditions."""
    df = wb.get_sheet(sheet)
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found. Available: {list(df.columns)}")

    mask = pd.Series([True] * len(df), index=df.index)

    if values is not None:
        mask &= df[column].isin(values)
    if contains is not None:
        mask &= df[column].astype(str).str.contains(contains, na=False, regex=False)
    if regex is not None:
        mask &= df[column].astype(str).str.contains(regex, na=False, regex=True)
    if equals is not None:
        mask &= df[column] == equals
    if not_equals is not None:
        mask &= df[column] != not_equals
    if greater_than is not None:
        mask &= df[column] > greater_than
    if less_than is not None:
        mask &= df[column] < less_than
    if greater_equal is not None:
        mask &= df[column] >= greater_equal
    if less_equal is not None:
        mask &= df[column] <= less_equal
    if between is not None:
        mask &= df[column].between(between[0], between[1])
    if is_null:
        mask &= df[column].isnull()
    if not_null:
        mask &= df[column].notnull()
    if startswith is not None:
        mask &= df[column].astype(str).str.startswith(startswith)
    if endswith is not None:
        mask &= df[column].astype(str).str.endswith(endswith)

    return df[mask]


def filter_multi(
    wb: SheetWorkbook,
    conditions: list[dict[str, Any]],
    logic: str = "and",
    sheet: str | int | None = None,
) -> pd.DataFrame:
    """Filter with multiple column conditions using AND/OR logic.

    Each condition dict supports keys:
        column, op, value where op is one of:
        eq, ne, gt, lt, ge, le, contains, startswith, endswith,
        regex, in, between, is_null, not_null
    """
    df = wb.get_sheet(sheet)
    masks = []

    for cond in conditions:
        col = cond["column"]
        op = cond.get("op", "eq")
        val = cond.get("value")

        if col not in df.columns:
            raise KeyError(f"Column '{col}' not found. Available: {list(df.columns)}")

        series = df[col]

        if op == "eq":
            m = series == val
        elif op == "ne":
            m = series != val
        elif op == "gt":
            m = series > val
        elif op == "lt":
            m = series < val
        elif op == "ge":
            m = series >= val
        elif op == "le":
            m = series <= val
        elif op == "contains":
            m = series.astype(str).str.contains(str(val), na=False, regex=False)
        elif op == "startswith":
            m = series.astype(str).str.startswith(str(val))
        elif op == "endswith":
            m = series.astype(str).str.endswith(str(val))
        elif op == "regex":
            m = series.astype(str).str.contains(str(val), na=False, regex=True)
        elif op == "in":
            m = series.isin(val if isinstance(val, list) else [val])
        elif op == "between":
            m = series.between(val[0], val[1])
        elif op == "is_null":
            m = series.isnull()
        elif op == "not_null":
            m = series.notnull()
        else:
            raise ValueError(f"Unknown filter op: {op}")

        masks.append(m)

    if logic == "and":
        combined = masks[0]
        for m in masks[1:]:
            combined &= m
    elif logic == "or":
        combined = masks[0]
        for m in masks[1:]:
            combined |= m
    else:
        raise ValueError(f"Logic must be 'and' or 'or', got '{logic}'")

    return df[combined]


def search_keyword(
    wb: SheetWorkbook,
    keyword: str,
    columns: list[str] | None = None,
    case_sensitive: bool = False,
    regex_mode: bool = False,
    sheet: str | int | None = None,
) -> pd.DataFrame:
    """Search for a keyword across specified columns (or all columns)."""
    df = wb.get_sheet(sheet)
    cols = columns or list(df.columns)
    mask = pd.Series([False] * len(df), index=df.index)

    flags = 0 if case_sensitive else re.IGNORECASE
    for col in cols:
        if col not in df.columns:
            continue
        if regex_mode:
            mask |= df[col].astype(str).str.contains(keyword, na=False, regex=True, flags=flags)
        else:
            pattern = re.escape(keyword)
            mask |= df[col].astype(str).str.contains(pattern, na=False, regex=True, flags=flags)

    return df[mask]


def get_unique_values(
    wb: SheetWorkbook,
    column: str,
    sort: bool = True,
    sheet: str | int | None = None,
) -> list[Any]:
    """Get unique values for a column - fast, for filter dropdown menus."""
    if sort:
        return wb.unique_values(column, sheet=sheet)
    return list(wb.get_sheet(sheet)[column].dropna().unique())


def auto_filter(
    wb: SheetWorkbook,
    column: str,
    top_n: int | None = None,
    bottom_n: int | None = None,
    above_avg: bool = False,
    below_avg: bool = False,
    top_percent: float | None = None,
    sheet: str | int | None = None,
) -> pd.DataFrame:
    """Excel-like auto-filter: top/bottom N, above/below average, top percent."""
    df = wb.get_sheet(sheet)
    series = df[column]

    if top_n is not None:
        return df.nlargest(top_n, column)
    if bottom_n is not None:
        return df.nsmallest(bottom_n, column)
    if above_avg:
        avg = series.mean()
        return df[series > avg]
    if below_avg:
        avg = series.mean()
        return df[series < avg]
    if top_percent is not None:
        threshold = series.quantile(1 - top_percent / 100)
        return df[series >= threshold]

    return df


def pivot_summary(
    wb: SheetWorkbook,
    index: str | list[str],
    values: str | list[str] | None = None,
    aggfunc: str = "mean",
    columns: str | list[str] | None = None,
    sheet: str | int | None = None,
) -> pd.DataFrame:
    """Create a pivot table summary like Excel's pivot table."""
    df = wb.get_sheet(sheet)
    pivot = pd.pivot_table(df, index=index, values=values, columns=columns, aggfunc=aggfunc)
    return pivot.reset_index()


def group_aggregate(
    wb: SheetWorkbook,
    group_by: str | list[str],
    agg_dict: dict[str, str | list[str]],
    sheet: str | int | None = None,
) -> pd.DataFrame:
    """Group by columns and aggregate - like Excel's subtotal feature."""
    df = wb.get_sheet(sheet)
    return df.groupby(group_by, as_index=False).agg(agg_dict)
