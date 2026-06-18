"""Comprehensive test suite for ChaBiao."""

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest


@pytest.fixture
def sample_df():
    return pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"],
            "City": [
                "Beijing",
                "Shanghai",
                "Beijing",
                "Guangzhou",
                "Shanghai",
                "Beijing",
                "Shenzhen",
                "Guangzhou",
            ],
            "Age": [25, 30, 35, 28, 42, 33, 29, 37],
            "Salary": [50000, 60000, 75000, 55000, 90000, 68000, 62000, 80000],
            "Department": [
                "Engineering",
                "Sales",
                "Engineering",
                "Marketing",
                "Engineering",
                "Sales",
                "Marketing",
                "Engineering",
            ],
        }
    )


@pytest.fixture
def sample_csv(sample_df, tmp_path):
    path = tmp_path / "test_data.csv"
    sample_df.to_csv(path, index=False)
    return str(path)


@pytest.fixture
def sample_xlsx(sample_df, tmp_path):
    path = tmp_path / "test_data.xlsx"
    sample_df.to_excel(path, index=False)
    return str(path)


@pytest.fixture
def second_csv(tmp_path):
    df = pd.DataFrame(
        {
            "Name": ["Alice", "Bob", "Charlie", "Diana", "Eve"],
            "Bonus": [5000, 6000, 7500, 5500, 9000],
        }
    )
    path = tmp_path / "test_bonus.csv"
    df.to_csv(path, index=False)
    return str(path)


class TestToolResult:
    def test_success_result(self):
        from chabiao.api import ToolResult

        r = ToolResult(success=True, data={"key": "value"})
        assert r.success is True
        assert r.data == {"key": "value"}
        assert r.error is None

    def test_failure_result(self):
        from chabiao.api import ToolResult

        r = ToolResult(success=False, error="something failed")
        assert r.success is False
        assert r.error == "something failed"

    def test_to_dict(self):
        from chabiao.api import ToolResult

        r = ToolResult(success=True, data=[1, 2])
        d = r.to_dict()
        assert set(d.keys()) == {"success", "data", "error", "metadata"}
        assert d["success"] is True
        assert d["data"] == [1, 2]

    def test_default_metadata_isolation(self):
        from chabiao.api import ToolResult

        r1 = ToolResult(success=True)
        r2 = ToolResult(success=True)
        r1.metadata["a"] = 1
        assert "a" not in r2.metadata

    def test_metadata_preserved(self):
        from chabiao.api import ToolResult

        r = ToolResult(success=True, data="ok", metadata={"version": "0.1.0"})
        d = r.to_dict()
        assert d["metadata"]["version"] == "0.1.0"


class TestCoreWorkbook:
    def test_load_csv(self, sample_csv):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_csv)
        assert wb.active_sheet is not None
        assert wb.shape() == (8, 5)

    def test_load_xlsx(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        assert wb.shape() == (8, 5)

    def test_sheet_names(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        assert len(wb.sheet_names) >= 1

    def test_columns(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        cols = wb.columns()
        assert "Name" in cols
        assert "City" in cols

    def test_head_tail(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        h = wb.head(3)
        assert len(h) == 3
        t = wb.tail(2)
        assert len(t) == 2

    def test_info_dict(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        info = wb.info_dict()
        assert info["rows"] == 8
        assert info["columns"] == 5

    def test_unique_values(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        cities = wb.unique_values("City")
        assert "Beijing" in cities
        assert "Shanghai" in cities

    def test_column_stats(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        stats = wb.column_stats("Salary")
        assert stats["mean"] > 0
        assert stats["min"] == 50000
        assert stats["max"] == 90000

    def test_sort_by(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        sorted_df = wb.sort_by("Age")
        assert sorted_df.iloc[0]["Age"] == 25

    def test_slice_range(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        sliced = wb.slice_range(2, 5)
        assert len(sliced) == 3

    def test_drop_duplicates(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        deduped = wb.drop_duplicates("City")
        assert len(deduped) == 4

    def test_rename_columns(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        renamed = wb.rename_columns({"Name": "Full Name"})
        assert "Full Name" in renamed.columns

    def test_to_csv(self, sample_xlsx, tmp_path):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        out = wb.to_csv(str(tmp_path / "output.csv"))
        assert out.exists()

    def test_to_json(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        result = wb.to_json()
        data = json.loads(result)
        assert len(data) == 8

    def test_unsupported_format(self, tmp_path):
        from chabiao.core import load_workbook

        bad_path = tmp_path / "test.pdf"
        bad_path.write_text("not a spreadsheet")
        with pytest.raises(ValueError, match="Unsupported"):
            load_workbook(str(bad_path))

    def test_set_active_sheet(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        first_sheet = wb.active_sheet
        if len(wb.sheet_names) > 1:
            wb.set_active(wb.sheet_names[1])
            assert wb.active_sheet != first_sheet


class TestFilters:
    def test_filter_contains(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "City", contains="Beijing")
        assert len(result) == 3

    def test_filter_equals(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Name", equals="Alice")
        assert len(result) == 1
        assert result.iloc[0]["Name"] == "Alice"

    def test_filter_greater_than(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Age", greater_than=35)
        assert all(result["Age"] > 35)

    def test_filter_between(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Salary", between=(55000, 75000))
        assert all((result["Salary"] >= 55000) & (result["Salary"] <= 75000))

    def test_filter_is_null(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Age", is_null=True)
        assert len(result) == 0

    def test_filter_not_null(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Name", not_null=True)
        assert len(result) == 8

    def test_filter_startswith(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Name", startswith="A")
        assert len(result) == 1

    def test_filter_endswith(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Name", endswith="e")
        assert len(result) >= 1

    def test_filter_values(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "City", values=["Beijing", "Shanghai"])
        assert all(c in ["Beijing", "Shanghai"] for c in result["City"])

    def test_filter_regex(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_column

        wb = load_workbook(sample_xlsx)
        result = filter_column(wb, "Name", regex="^[A-F]")
        assert all(n.startswith(tuple("ABCDEF")) for n in result["Name"])

    def test_search_keyword(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import search_keyword

        wb = load_workbook(sample_xlsx)
        result = search_keyword(wb, "Beijing")
        assert len(result) >= 3

    def test_search_keyword_columns(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import search_keyword

        wb = load_workbook(sample_xlsx)
        result = search_keyword(wb, "Beijing", columns=["City"])
        assert len(result) >= 3

    def test_filter_multi_and(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_multi

        wb = load_workbook(sample_xlsx)
        result = filter_multi(
            wb,
            [
                {"column": "City", "op": "eq", "value": "Beijing"},
                {"column": "Age", "op": "gt", "value": 30},
            ],
            logic="and",
        )
        assert all((result["City"] == "Beijing") & (result["Age"] > 30))

    def test_filter_multi_or(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import filter_multi

        wb = load_workbook(sample_xlsx)
        result = filter_multi(
            wb,
            [
                {"column": "City", "op": "eq", "value": "Beijing"},
                {"column": "City", "op": "eq", "value": "Shanghai"},
            ],
            logic="or",
        )
        assert all(result["City"].isin(["Beijing", "Shanghai"]))

    def test_auto_filter_top_n(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import auto_filter

        wb = load_workbook(sample_xlsx)
        result = auto_filter(wb, "Salary", top_n=3)
        assert len(result) == 3

    def test_auto_filter_above_avg(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import auto_filter

        wb = load_workbook(sample_xlsx)
        result = auto_filter(wb, "Salary", above_avg=True)
        assert all(result["Salary"] > 67500)

    def test_group_aggregate(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import group_aggregate

        wb = load_workbook(sample_xlsx)
        result = group_aggregate(wb, "City", {"Salary": "mean"})
        assert len(result) == 4

    def test_pivot_summary(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.filters import pivot_summary

        wb = load_workbook(sample_xlsx)
        result = pivot_summary(wb, index="City", values="Salary", aggfunc="mean")
        assert len(result) == 4


class TestSpotlight:
    def test_spotlight_row(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.spotlight import spotlight

        wb = load_workbook(sample_xlsx)
        result = spotlight(wb, row=0)
        assert result["row_index"] == 0
        assert result["row_data"]["Name"] == "Alice"

    def test_spotlight_with_column(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.spotlight import spotlight

        wb = load_workbook(sample_xlsx)
        result = spotlight(wb, row=0, column="Salary")
        assert "column_stats" in result
        assert result["column_stats"]["name"] == "Salary"

    def test_spotlight_cell(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.spotlight import spotlight_cell

        wb = load_workbook(sample_xlsx)
        result = spotlight_cell(wb, row=0, column="Name")
        assert result["cell"]["value"] == "Alice"

    def test_spotlight_cell_stats(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.spotlight import spotlight_cell

        wb = load_workbook(sample_xlsx)
        result = spotlight_cell(wb, row=0, column="Salary")
        assert "mean" in result["column_info"]
        assert result["column_info"]["unique_count"] == 8

    def test_spotlight_range(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.spotlight import spotlight_range

        wb = load_workbook(sample_xlsx)
        result = spotlight_range(wb, start_row=0, end_row=3)
        assert result["row_count"] == 3
        assert result["start_row"] == 0

    def test_cross_reference(self, sample_xlsx):
        from chabiao.core import load_workbook
        from chabiao.spotlight import cross_reference

        wb = load_workbook(sample_xlsx)
        result = cross_reference(wb, "Beijing", source_columns=["City"])
        assert result["total_matches"] == 3


class TestAPIFunctions:
    def test_open_file_csv(self, sample_csv):
        from chabiao.api import open_file

        result = open_file(input_path=sample_csv)
        assert result.success is True
        assert result.data["info"]["rows"] == 8

    def test_open_file_xlsx(self, sample_xlsx):
        from chabiao.api import open_file

        result = open_file(input_path=sample_xlsx)
        assert result.success is True

    def test_open_file_not_found(self):
        from chabiao.api import open_file

        result = open_file(input_path="/nonexistent/file.xlsx")
        assert result.success is False
        assert result.error is not None

    def test_filter_data_contains(self, sample_xlsx):
        from chabiao.api import filter_data

        result = filter_data(input_path=sample_xlsx, column="City", contains="Beijing")
        assert result.success is True
        assert result.data["total_rows"] == 3

    def test_filter_data_equals(self, sample_xlsx):
        from chabiao.api import filter_data

        result = filter_data(input_path=sample_xlsx, column="Name", equals="Alice")
        assert result.success is True
        assert result.data["total_rows"] == 1

    def test_filter_data_top_n(self, sample_xlsx):
        from chabiao.api import filter_data

        result = filter_data(input_path=sample_xlsx, column="Salary", top_n=3)
        assert result.success is True
        assert result.data["total_rows"] == 3

    def test_search_data(self, sample_xlsx):
        from chabiao.api import search_data

        result = search_data(input_path=sample_xlsx, keyword="Beijing")
        assert result.success is True
        assert result.data["total_matches"] >= 3

    def test_aggregate_data(self, sample_xlsx):
        from chabiao.api import aggregate_data

        result = aggregate_data(
            input_path=sample_xlsx,
            group_by="City",
            aggregations={"Salary": "mean"},
        )
        assert result.success is True
        assert result.data["total_groups"] == 4

    def test_compare_data(self, sample_xlsx, second_csv):
        from chabiao.api import compare_data

        result = compare_data(
            input_path=sample_xlsx,
            other_path=second_csv,
            on="Name",
            how="inner",
        )
        assert result.success is True

    def test_export_data(self, sample_xlsx, tmp_path):
        from chabiao.api import export_data

        out_path = str(tmp_path / "output.csv")
        result = export_data(input_path=sample_xlsx, output_path=out_path, output_format="csv")
        assert result.success is True
        assert Path(out_path).exists()

    def test_spotlight_api(self, sample_xlsx):
        from chabiao.api import spotlight

        result = spotlight(input_path=sample_xlsx, row=0)
        assert result.success is True
        assert result.data["row_data"]["Name"] == "Alice"

    def test_filter_with_output(self, sample_xlsx, tmp_path):
        from chabiao.api import filter_data

        out_path = str(tmp_path / "filtered.csv")
        result = filter_data(
            input_path=sample_xlsx,
            column="City",
            contains="Beijing",
            output_path=out_path,
            output_format="csv",
        )
        assert result.success is True
        assert Path(out_path).exists()


class TestToolsSchema:
    def test_tool_structure(self):
        from chabiao.tools import TOOLS

        for tool in TOOLS:
            assert tool["type"] == "function"
            func = tool["function"]
            assert "name" in func
            assert "description" in func
            assert "parameters" in func

    def test_required_fields_in_properties(self):
        from chabiao.tools import TOOLS

        for tool in TOOLS:
            func = tool["function"]
            props = func["parameters"]["properties"]
            for req in func["parameters"]["required"]:
                assert req in props

    def test_all_tools_have_names(self):
        from chabiao.tools import TOOLS

        names = [t["function"]["name"] for t in TOOLS]
        assert "chabiao_open_file" in names
        assert "chabiao_filter_data" in names
        assert "chabiao_search_data" in names
        assert "chabiao_aggregate_data" in names
        assert "chabiao_compare_data" in names
        assert "chabiao_export_data" in names
        assert "chabiao_spotlight" in names


class TestToolsDispatch:
    def test_dispatch_open_file(self, sample_csv):
        from chabiao.tools import dispatch

        result = dispatch("chabiao_open_file", {"input_path": sample_csv})
        assert result["success"] is True

    def test_dispatch_filter_data(self, sample_xlsx):
        from chabiao.tools import dispatch

        result = dispatch(
            "chabiao_filter_data",
            {"input_path": sample_xlsx, "column": "City", "contains": "Beijing"},
        )
        assert result["success"] is True

    def test_dispatch_search_data(self, sample_xlsx):
        from chabiao.tools import dispatch

        result = dispatch("chabiao_search_data", {"input_path": sample_xlsx, "keyword": "Alice"})
        assert result["success"] is True

    def test_dispatch_unknown_tool(self):
        from chabiao.tools import dispatch

        with pytest.raises(ValueError, match="Unknown tool"):
            dispatch("nonexistent_tool", {})

    def test_dispatch_json_string_args(self, sample_xlsx):
        from chabiao.tools import dispatch

        result = dispatch(
            "chabiao_search_data", json.dumps({"input_path": sample_xlsx, "keyword": "Beijing"})
        )
        assert result["success"] is True


class TestCLIFlags:
    def _run_cli(self, *args):
        return subprocess.run(
            [sys.executable, "-m", "chabiao"] + list(args),
            capture_output=True,
            text=True,
            timeout=30,
        )

    def test_version_flag(self):
        r = self._run_cli("-V")
        assert r.returncode == 0
        assert "chabiao" in r.stdout.lower() or "0.1.0" in r.stdout

    def test_help_has_unified_flags(self):
        r = self._run_cli("--help")
        assert "--json" in r.stdout
        assert "--quiet" in r.stdout or "-q" in r.stdout

    def test_help_has_commands(self):
        r = self._run_cli("--help")
        assert "open" in r.stdout
        assert "filter" in r.stdout
        assert "search" in r.stdout


class TestPackageExports:
    def test_version(self):
        from chabiao import __version__

        assert __version__ == "0.1.0"

    def test_tool_result_import(self):
        from chabiao import ToolResult

        r = ToolResult(success=True)
        assert r.success is True

    def test_api_functions_import(self):
        from chabiao import (
            open_file,
            filter_data,
            search_data,
            aggregate_data,
            compare_data,
            export_data,
            spotlight_view,
        )

        assert callable(open_file)
        assert callable(filter_data)
        assert callable(search_data)
        assert callable(aggregate_data)
        assert callable(compare_data)
        assert callable(export_data)
        assert callable(spotlight_view)

    def test_tools_import(self):
        from chabiao.tools import TOOLS, dispatch

        assert isinstance(TOOLS, list)
        assert callable(dispatch)


class TestMergeConcat:
    def test_merge_files(self, sample_xlsx, second_csv):
        from chabiao.core import merge_files

        result = merge_files([sample_xlsx, second_csv], on="Name", how="inner")
        assert "Salary" in result.columns
        assert "Bonus" in result.columns

    def test_concat_files(self, sample_csv, second_csv):
        from chabiao.core import concat_files

        result = concat_files([sample_csv, sample_csv])
        assert len(result) == 16


class TestDataTransformations:
    def test_fill_na(self, tmp_path):
        from chabiao.core import load_workbook

        df = pd.DataFrame({"A": [1, None, 3], "B": ["x", None, "z"]})
        path = tmp_path / "nan_data.csv"
        df.to_csv(path, index=False)
        wb = load_workbook(str(path))
        result = wb.fill_na(value=0, column="A")
        assert result["A"].iloc[1] == 0

    def test_replace_values(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        result = wb.replace_values("City", "Beijing", "BJ")
        assert "BJ" in result["City"].values

    def test_add_column(self, sample_xlsx):
        from chabiao.core import load_workbook

        wb = load_workbook(sample_xlsx)
        result = wb.add_column("Bonus", formula="Salary * 0.1")
        assert "Bonus" in result.columns
