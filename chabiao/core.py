"""Core data engine for ChaBiao - fast spreadsheet loading and manipulation.

Uses multi-threading and optimized pandas settings for fast loading
of large spreadsheet files (15MB+, 20K+ rows).
"""

from __future__ import annotations

import logging
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Sequence

import pandas as pd

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {".xlsx", ".xls", ".csv", ".tsv", ".ods", ".xlsm", ".xlsb"}

FORMAT_READERS: dict[str, dict[str, Any]] = {
    ".xlsx": {"engine": "openpyxl"},
    ".xls": {"engine": "xlrd"},
    ".xlsm": {"engine": "openpyxl"},
    ".xlsb": {"engine": "pyxlsb"},
    ".csv": {},
    ".tsv": {"sep": "\t"},
    ".ods": {"engine": "odf"},
}

_MAX_WORKERS = min(os.cpu_count() or 4, 8)


def _optimize_pandas() -> None:
    """Apply performance-optimized pandas settings."""
    try:
        pd.options.mode.dtype_backend = "pyarrow"
    except (pd.errors.OptionError, AttributeError):
        pass


_optimize_pandas()


def detect_format(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix not in SUPPORTED_FORMATS:
        supported = ", ".join(sorted(SUPPORTED_FORMATS))
        raise ValueError(f"Unsupported file format: {suffix}. Supported: {supported}")
    return suffix


def _load_sheet(xls: pd.ExcelFile, sname: str) -> tuple[str, pd.DataFrame]:
    """Load a single sheet - used for parallel loading."""
    df = pd.read_excel(xls, sheet_name=sname)
    return sname, df


class SheetWorkbook:
    """Represents a loaded workbook with one or more sheets.

    Multi-sheet workbooks load sheets in parallel using ThreadPoolExecutor.
    """

    def __init__(self, path: str | Path, sheet_name: str | int | None = None):
        self.path = Path(path)
        self.format = detect_format(self.path)
        self._sheets: dict[str, pd.DataFrame] = {}
        self._sheet_names: list[str] = []
        self._active_sheet: str | None = None
        self._load(sheet_name)

    def _load(self, sheet_name: str | int | None = None) -> None:
        suffix = self.format
        kwargs = dict(FORMAT_READERS.get(suffix, {}))

        if suffix in {".csv", ".tsv"}:
            df = pd.read_csv(self.path, **kwargs)
            name = self.path.stem
            self._sheets[name] = df
            self._sheet_names = [name]
            self._active_sheet = name
        else:
            xls = pd.ExcelFile(self.path, **kwargs)
            self._sheet_names = list(xls.sheet_names)

            if sheet_name is not None:
                if isinstance(sheet_name, int):
                    sheet_name = self._sheet_names[sheet_name]
                df = pd.read_excel(xls, sheet_name=sheet_name)
                self._sheets[sheet_name] = df
                self._active_sheet = sheet_name
            elif len(self._sheet_names) > 1:
                # Load all sheets in parallel
                with ThreadPoolExecutor(max_workers=_MAX_WORKERS) as pool:
                    futures = {
                        pool.submit(_load_sheet, xls, sname): sname
                        for sname in self._sheet_names
                    }
                    for future in as_completed(futures):
                        sname, df = future.result()
                        self._sheets[sname] = df
                self._active_sheet = self._sheet_names[0]
            else:
                sname = self._sheet_names[0]
                self._sheets[sname] = pd.read_excel(xls, sheet_name=sname)
                self._active_sheet = sname

            xls.close()

    @property
    def sheet_names(self) -> list[str]:
        return list(self._sheet_names)

    @property
    def active_sheet(self) -> str | None:
        return self._active_sheet

    @property
    def active_df(self) -> pd.DataFrame:
        if self._active_sheet is None:
            raise ValueError("No active sheet")
        return self._sheets[self._active_sheet]

    def set_active(self, name: str) -> None:
        if name not in self._sheet_names:
            raise KeyError(f"Sheet '{name}' not found. Available: {self._sheet_names}")
        self._active_sheet = name

    def get_sheet(self, name: str | int | None = None) -> pd.DataFrame:
        if name is None:
            return self.active_df
        if isinstance(name, int):
            name = self._sheet_names[name]
        if name not in self._sheets:
            raise KeyError(f"Sheet '{name}' not loaded. Available: {list(self._sheets.keys())}")
        return self._sheets[name]

    def columns(self, sheet: str | int | None = None) -> list[str]:
        df = self.get_sheet(sheet)
        return list(df.columns)

    def dtypes_info(self, sheet: str | int | None = None) -> dict[str, str]:
        df = self.get_sheet(sheet)
        return {col: str(dtype) for col, dtype in df.dtypes.items()}

    def shape(self, sheet: str | int | None = None) -> tuple[int, int]:
        df = self.get_sheet(sheet)
        return df.shape

    def head(self, n: int = 10, sheet: str | int | None = None) -> pd.DataFrame:
        return self.get_sheet(sheet).head(n)

    def tail(self, n: int = 10, sheet: str | int | None = None) -> pd.DataFrame:
        return self.get_sheet(sheet).tail(n)

    def info_dict(self, sheet: str | int | None = None) -> dict[str, Any]:
        df = self.get_sheet(sheet)
        return {
            "rows": len(df),
            "columns": len(df.columns),
            "column_names": list(df.columns),
            "dtypes": {col: str(dt) for col, dt in df.dtypes.items()},
            "null_counts": df.isnull().sum().to_dict(),
            "memory_mb": df.memory_usage(deep=True).sum() / 1024 / 1024,
        }

    def unique_values(self, column: str, sheet: str | int | None = None) -> list[Any]:
        df = self.get_sheet(sheet)
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found. Available: {list(df.columns)}")
        return sorted(df[column].dropna().unique().tolist())

    def column_stats(self, column: str, sheet: str | int | None = None) -> dict[str, Any]:
        df = self.get_sheet(sheet)
        if column not in df.columns:
            raise KeyError(f"Column '{column}' not found. Available: {list(df.columns)}")
        series = df[column]
        stats: dict[str, Any] = {
            "column": column,
            "dtype": str(series.dtype),
            "count": int(series.count()),
            "null_count": int(series.isnull().sum()),
            "unique_count": int(series.nunique()),
        }
        if pd.api.types.is_numeric_dtype(series):
            desc = series.describe()
            stats["mean"] = float(desc["mean"])
            stats["std"] = float(desc["std"])
            stats["min"] = float(desc["min"])
            stats["25%"] = float(desc["25%"])
            stats["50%"] = float(desc["50%"])
            stats["75%"] = float(desc["75%"])
            stats["max"] = float(desc["max"])
        return stats

    def slice_range(
        self,
        start_row: int = 0,
        end_row: int | None = None,
        columns: list[str] | None = None,
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet)
        if end_row is None:
            end_row = len(df)
        df = df.iloc[start_row:end_row]
        if columns:
            df = df[columns]
        return df

    def sort_by(
        self,
        columns: str | list[str],
        ascending: bool | list[bool] = True,
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet)
        return df.sort_values(by=columns, ascending=ascending)

    def replace_values(
        self,
        column: str,
        to_replace: Any,
        value: Any,
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet).copy()
        df[column] = df[column].replace(to_replace, value)
        return df

    def fill_na(
        self,
        value: Any = None,
        column: str | None = None,
        method: str | None = None,
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet).copy()
        if column:
            if method:
                df[column] = df[column].fillna(method=method)
            else:
                df[column] = df[column].fillna(value)
        else:
            if method:
                df = df.fillna(method=method)
            else:
                df = df.fillna(value)
        return df

    def drop_duplicates(
        self,
        columns: str | list[str] | None = None,
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet)
        return df.drop_duplicates(subset=columns)

    def drop_na(
        self,
        columns: str | list[str] | None = None,
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet)
        return df.dropna(subset=columns)

    def rename_columns(
        self,
        mapping: dict[str, str],
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet).copy()
        return df.rename(columns=mapping)

    def add_column(
        self,
        name: str,
        value: Any = None,
        formula: str | None = None,
        sheet: str | int | None = None,
    ) -> pd.DataFrame:
        df = self.get_sheet(sheet).copy()
        if formula:
            df[name] = df.eval(formula)
        else:
            df[name] = value
        return df

    def to_csv(self, path: str | Path, sheet: str | int | None = None, **kwargs: Any) -> Path:
        df = self.get_sheet(sheet)
        out = Path(path)
        df.to_csv(out, index=False, **kwargs)
        return out

    def to_excel(self, path: str | Path, sheet: str | int | None = None, **kwargs: Any) -> Path:
        df = self.get_sheet(sheet)
        out = Path(path)
        df.to_excel(out, index=False, **kwargs)
        return out

    def to_json(
        self,
        path: str | Path | None = None,
        sheet: str | int | None = None,
        **kwargs: Any,
    ) -> str | Path:
        df = self.get_sheet(sheet)
        json_str = df.to_json(orient="records", force_ascii=False, **kwargs)
        if path:
            out = Path(path)
            out.write_text(json_str, encoding="utf-8")
            return out
        return json_str


def load_workbook(path: str | Path, sheet_name: str | int | None = None) -> SheetWorkbook:
    """Load a spreadsheet file into a SheetWorkbook object."""
    return SheetWorkbook(path, sheet_name=sheet_name)


def quick_view(path: str | Path, n: int = 10, sheet: str | int | None = None) -> dict[str, Any]:
    """Quickly load and view the first n rows of a spreadsheet."""
    wb = load_workbook(path, sheet_name=sheet)
    info = wb.info_dict(sheet)
    preview = wb.head(n, sheet)
    return {
        "info": info,
        "preview": preview.to_dict(orient="records"),
    }


def _load_file(p: str | Path) -> pd.DataFrame:
    """Load a single file - used for parallel merge/concat."""
    wb = load_workbook(p)
    return wb.active_df


def merge_files(
    paths: Sequence[str | Path],
    on: str | list[str] | None = None,
    how: str = "inner",
    sort: bool = False,
) -> pd.DataFrame:
    """Merge multiple spreadsheet files by key columns.

    Loads files in parallel using ThreadPoolExecutor.
    """
    with ThreadPoolExecutor(max_workers=min(len(paths), _MAX_WORKERS)) as pool:
        dfs = list(pool.map(_load_file, paths))

    result = dfs[0]
    for df in dfs[1:]:
        if on:
            result = result.merge(df, on=on, how=how, sort=sort)
        else:
            result = pd.concat([result, df], ignore_index=True, sort=sort)
    return result


def concat_files(
    paths: Sequence[str | Path],
    ignore_index: bool = True,
) -> pd.DataFrame:
    """Concatenate multiple spreadsheet files vertically.

    Loads files in parallel using ThreadPoolExecutor.
    """
    with ThreadPoolExecutor(max_workers=min(len(paths), _MAX_WORKERS)) as pool:
        dfs = list(pool.map(_load_file, paths))
    return pd.concat(dfs, ignore_index=ignore_index)