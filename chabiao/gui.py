"""PySide6 GUI interface for ChaBiao - fast interactive spreadsheet viewer."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pandas as pd

from .__version__ import __version__
from .core import SheetWorkbook, load_workbook


def _import_pyside6():
    try:
        from PySide6 import QtCore, QtGui, QtWidgets

        return QtWidgets, QtCore, QtGui
    except ImportError:
        print("PySide6 is required for GUI mode. Install with: pip install chabiao[gui]")
        sys.exit(1)


class SpreadsheetModel:
    """Data model for managing loaded spreadsheets."""

    def __init__(self) -> None:
        self.workbook: SheetWorkbook | None = None
        self._filtered_df = None
        self._spotlight_row: int | None = None
        self._spotlight_col: str | None = None

    def load(self, path: str, sheet_name: str | int | None = None) -> dict[str, Any]:
        self.workbook = load_workbook(path, sheet_name=sheet_name)
        self._filtered_df = None
        return self.workbook.info_dict()

    @property
    def current_df(self):
        if self._filtered_df is not None:
            return self._filtered_df
        if self.workbook:
            return self.workbook.active_df
        return None

    def set_filter(self, column: str, keyword: str, mode: str = "contains") -> int:
        from .filters import filter_column, search_keyword

        if not self.workbook:
            return 0
        if mode == "contains":
            self._filtered_df = filter_column(self.workbook, column, contains=keyword)
        elif mode == "regex":
            self._filtered_df = filter_column(self.workbook, column, regex=keyword)
        elif mode == "equals":
            self._filtered_df = filter_column(self.workbook, column, equals=keyword)
        else:
            self._filtered_df = search_keyword(self.workbook, keyword, columns=[column])
        return len(self._filtered_df)

    def clear_filter(self):
        self._filtered_df = None

    def set_spotlight(self, row: int, column: str | None = None):
        self._spotlight_row = row
        self._spotlight_col = column


class ChaBiaoWindow:
    """Main application window for ChaBiao GUI."""

    def __init__(self) -> None:
        QtWidgets, QtCore, QtGui = _import_pyside6()

        self.app = QtWidgets.QApplication(sys.argv)
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle(f"ChaBiao 查表 v{__version__}")
        self.window.setMinimumSize(1200, 800)

        self.model = SpreadsheetModel()
        self._QtWidgets = QtWidgets
        self._QtCore = QtCore
        self._QtGui = QtGui
        self._spotlight_active = False

        self._setup_ui(QtWidgets, QtCore, QtGui)
        self._setup_menu(QtWidgets, QtGui)

    def _setup_ui(self, QtWidgets, QtCore, QtGui) -> None:
        central = QtWidgets.QWidget()
        self.window.setCentralWidget(central)
        layout = QtWidgets.QVBoxLayout(central)

        # Toolbar area
        toolbar = QtWidgets.QHBoxLayout()
        self.path_label = QtWidgets.QLabel("No file loaded")
        self.path_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 5px;")
        toolbar.addWidget(self.path_label)
        self.info_label = QtWidgets.QLabel("")
        self.info_label.setStyleSheet("color: gray; padding: 5px;")
        toolbar.addWidget(self.info_label)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Sheet tabs
        self.sheet_tabs = QtWidgets.QTabWidget()
        layout.addWidget(self.sheet_tabs)

        # Filter bar
        filter_bar = QtWidgets.QHBoxLayout()
        self.filter_column = QtWidgets.QComboBox()
        self.filter_column.setMinimumWidth(150)
        self.filter_column.setEditable(True)
        filter_bar.addWidget(QtWidgets.QLabel("Column:"))
        filter_bar.addWidget(self.filter_column)

        self.filter_keyword = QtWidgets.QLineEdit()
        self.filter_keyword.setPlaceholder("Type to filter / 输入筛选关键词...")
        self.filter_keyword.returnPressed.connect(self._do_filter)
        filter_bar.addWidget(self.filter_keyword, stretch=3)

        self.filter_mode = QtWidgets.QComboBox()
        self.filter_mode.addItems(["contains", "equals", "regex", "search"])
        filter_bar.addWidget(self.filter_mode)

        filter_btn = QtWidgets.QPushButton("Filter 筛选")
        filter_btn.clicked.connect(self._do_filter)
        filter_bar.addWidget(filter_btn)

        clear_btn = QtWidgets.QPushButton("Clear 清除")
        clear_btn.clicked.connect(self._clear_filter)
        filter_bar.addWidget(clear_btn)

        self.result_label = QtWidgets.QLabel("")
        self.result_label.setStyleSheet("color: #2196F3; font-weight: bold;")
        filter_bar.addWidget(self.result_label)
        layout.addLayout(filter_bar)

        # Table
        self.table = QtWidgets.QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        layout.addWidget(self.table)

        # Status bar
        self.window.statusBar().showMessage(
            "Ready / 就绪 - Open a file to start / 打开文件开始使用"
        )

    def _setup_menu(self, QtWidgets, QtGui) -> None:
        menubar = self.window.menuBar()

        file_menu = menubar.addMenu("&File 文件")
        open_action = QtGui.QAction("&Open 打开", self.window)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        export_action = QtGui.QAction("&Export 导出", self.window)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_file)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        quit_action = QtGui.QAction("&Quit 退出", self.window)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.window.close)
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu("&Edit 编辑")
        copy_action = QtGui.QAction("&Copy 复制", self.window)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self._copy_selection)
        edit_menu.addAction(copy_action)

        select_all_action = QtGui.QAction("Select &All 全选", self.window)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.table.selectAll)
        edit_menu.addAction(select_all_action)

        view_menu = menubar.addMenu("&View 视图")
        spotlight_action = QtGui.QAction("&Spotlight 聚光灯", self.window)
        spotlight_action.setShortcut("F6")
        spotlight_action.triggered.connect(self._toggle_spotlight)
        view_menu.addAction(spotlight_action)

    def _load_data_to_table(self, df) -> None:
        QtWidgets = self._QtWidgets
        QtCore = self._QtCore

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))

        for i, col in enumerate(df.columns):
            for j in range(len(df)):
                val = df.iloc[j, i]
                text = str(val) if pd.notna(val) else ""
                item = QtWidgets.QTableWidgetItem(text)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(j, i, item)

        self.table.resizeColumnsToContents()
        self.filter_column.clear()
        self.filter_column.addItems(list(df.columns))

    def _open_file(self) -> None:
        QtWidgets = self._QtWidgets
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            "Open Spreadsheet / 打开表格",
            "",
            "Spreadsheets (*.xlsx *.xls *.csv *.tsv *.xlsm);;All Files (*)",
        )
        if path:
            try:
                info = self.model.load(path)
                self.path_label.setText(Path(path).name)
                cols_preview = ", ".join(info["column_names"][:5])
                self.info_label.setText(
                    f"{info['rows']} rows × {info['columns']} cols | Sheets: {cols_preview}..."
                )
                self._load_data_to_table(self.model.current_df)
                self.window.statusBar().showMessage(f"Loaded: {path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.window, "Error", str(e))

    def _export_file(self) -> None:
        QtWidgets = self._QtWidgets
        if self.model.current_df is None:
            QtWidgets.QMessageBox.warning(self.window, "Warning", "No data to export")
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            "Export / 导出",
            "",
            "Excel (*.xlsx);;CSV (*.csv);;JSON (*.json)",
        )
        if path:
            try:
                df = self.model.current_df
                if path.endswith(".csv"):
                    df.to_csv(path, index=False)
                elif path.endswith(".json"):
                    Path(path).write_text(df.to_json(orient="records", force_ascii=False))
                else:
                    df.to_excel(path, index=False)
                self.window.statusBar().showMessage(f"Exported: {path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.window, "Error", str(e))

    def _do_filter(self) -> None:
        col = self.filter_column.currentText()
        keyword = self.filter_keyword.text()
        mode = self.filter_mode.currentText()
        if not col or not keyword:
            return
        try:
            count = self.model.set_filter(col, keyword, mode)
            self.result_label.setText(f"{count} results")
            self._load_data_to_table(self.model.current_df)
            msg = f"Filtered: {count} rows matching '{keyword}' in '{col}'"
            self.window.statusBar().showMessage(msg)
        except Exception as e:
            self.result_label.setText(f"Error: {e}")

    def _clear_filter(self) -> None:
        self.model.clear_filter()
        self.filter_keyword.clear()
        self.result_label.setText("")
        if self.model.workbook:
            self._load_data_to_table(self.model.current_df)
            self.window.statusBar().showMessage("Filter cleared")

    def _toggle_spotlight(self) -> None:
        self._spotlight_active = not self._spotlight_active
        if self._spotlight_active:
            msg = "Spotlight ON / 聚光灯已开启 - Click a cell to highlight row/col"
            self.window.statusBar().showMessage(msg)
            self.table.currentCellChanged.connect(self._apply_spotlight)
        else:
            self.window.statusBar().showMessage("Spotlight OFF / 聚光灯已关闭")
            try:
                self.table.currentCellChanged.disconnect(self._apply_spotlight)
            except Exception:
                pass
            self._remove_spotlight()

    def _apply_spotlight(self, row: int, col: int) -> None:
        QtGui = self._QtGui
        self._remove_spotlight()
        light_bg = QtGui.QBrush(QtGui.QColor(255, 255, 224))
        focus_bg = QtGui.QBrush(QtGui.QColor(255, 235, 59))
        for c in range(self.table.columnCount()):
            item = self.table.item(row, c)
            if item:
                item.setBackground(light_bg)
        for r in range(self.table.rowCount()):
            item = self.table.item(r, col)
            if item:
                item.setBackground(light_bg)
        focus_item = self.table.item(row, col)
        if focus_item:
            focus_item.setBackground(focus_bg)

    def _remove_spotlight(self) -> None:
        QtGui = self._QtGui
        default_bg = QtGui.QBrush()
        for r in range(self.table.rowCount()):
            for c in range(self.table.columnCount()):
                item = self.table.item(r, c)
                if item:
                    item.setBackground(default_bg)

    def _copy_selection(self) -> None:
        QtWidgets = self._QtWidgets
        selection = self.table.selectedRanges()
        if not selection:
            return
        rows = []
        for sel_range in selection:
            for r in range(sel_range.topRow(), sel_range.bottomRow() + 1):
                row_data = []
                for c in range(sel_range.leftColumn(), sel_range.rightColumn() + 1):
                    item = self.table.item(r, c)
                    row_data.append(item.text() if item else "")
                rows.append("\t".join(row_data))
        QtWidgets.QApplication.clipboard().setText("\n".join(rows))
        self.window.statusBar().showMessage("Copied to clipboard / 已复制到剪贴板")

    def _context_menu(self, pos) -> None:
        QtWidgets = self._QtWidgets
        menu = QtWidgets.QMenu()
        copy_action = menu.addAction("Copy / 复制")
        copy_action.triggered.connect(self._copy_selection)
        spotlight_action = menu.addAction("Toggle Spotlight / 聚光灯")
        spotlight_action.triggered.connect(self._toggle_spotlight)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def run(self) -> None:
        self.window.show()
        sys.exit(self.app.exec())


def main() -> None:
    window = ChaBiaoWindow()
    window.run()


if __name__ == "__main__":
    main()
