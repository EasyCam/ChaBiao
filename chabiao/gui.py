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


PAGE_SIZE = 500

_STYLESHEET = """
QMainWindow { background: #f8f9fa; }
QLabel { color: #333; }
QPushButton {
    background: #1976D2; color: white; border: none;
    padding: 5px 14px; border-radius: 4px; font-size: 13px;
}
QPushButton:hover { background: #1565C0; }
QPushButton:pressed { background: #0D47A1; }
QPushButton#clearBtn {
    background: #78909C; color: white;
}
QPushButton#clearBtn:hover { background: #607D8B; }
QPushButton#pageBtn {
    background: #e0e0e0; color: #333; padding: 3px 10px;
}
QPushButton#pageBtn:hover { background: #bdbdbd; }
QComboBox {
    padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px;
    background: white; min-width: 100px;
}
QLineEdit {
    padding: 4px 8px; border: 1px solid #ccc; border-radius: 4px;
    background: white;
}
QTableWidget {
    gridline-color: #e0e0e0; border: 1px solid #ddd;
    selection-background-color: #BBDEFB;
}
QHeaderView::section {
    background: #1976D2; color: white; padding: 6px 10px;
    border: none; font-weight: 500;
}
QStatusBar { background: #f5f5f5; color: #666; }
QTabBar::tab {
    background: #e0e0e0; padding: 6px 16px; border-top-left-radius: 4px;
    border-top-right-radius: 4px; margin-right: 2px;
}
QTabBar::tab:selected { background: white; font-weight: bold; }
"""


class SpreadsheetModel:
    """Data model for managing loaded spreadsheets."""

    def __init__(self) -> None:
        self.workbook: SheetWorkbook | None = None
        self._filtered_df: pd.DataFrame | None = None
        self._full_df: pd.DataFrame | None = None

    def load(self, path: str, sheet_name: str | int | None = None) -> dict[str, Any]:
        self.workbook = load_workbook(path, sheet_name=sheet_name)
        self._full_df = self.workbook.active_df.copy()
        self._filtered_df = None
        return self.workbook.info_dict()

    @property
    def current_df(self) -> pd.DataFrame | None:
        if self._filtered_df is not None:
            return self._filtered_df
        return self._full_df

    def set_filter(self, column: str, keyword: str, mode: str = "contains") -> int:
        from .filters import filter_column, search_keyword
        if not self.workbook:
            return 0
        wb = self.workbook
        if mode == "contains":
            self._filtered_df = filter_column(wb, column, contains=keyword)
        elif mode == "regex":
            self._filtered_df = filter_column(wb, column, regex=keyword)
        elif mode == "equals":
            self._filtered_df = filter_column(wb, column, equals=keyword)
        else:
            self._filtered_df = search_keyword(wb, keyword, columns=[column])
        return len(self._filtered_df)

    def clear_filter(self):
        self._filtered_df = None

    @property
    def is_filtered(self) -> bool:
        return self._filtered_df is not None

    @property
    def total_rows(self) -> int:
        return len(self._full_df) if self._full_df is not None else 0


class ChaBiaoWindow:
    """Main application window for ChaBiao GUI."""

    def __init__(self) -> None:
        QtWidgets, QtCore, QtGui = _import_pyside6()

        self.app = QtWidgets.QApplication(sys.argv)
        self.app.setStyleSheet(_STYLESHEET)
        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle(f"ChaBiao 查表 v{__version__}")
        self.window.setMinimumSize(1000, 650)
        self.window.resize(1280, 800)

        self.model = SpreadsheetModel()
        self._QtWidgets = QtWidgets
        self._QtCore = QtCore
        self._QtGui = QtGui
        self._spotlight_active = False
        self._current_page = 0
        self._page_size = PAGE_SIZE

        self._setup_ui(QtWidgets, QtCore, QtGui)
        self._setup_menu(QtWidgets, QtGui)

    def _setup_ui(self, QtWidgets, QtCore, QtGui) -> None:
        central = QtWidgets.QWidget()
        self.window.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)

        # --- Compact header: file info ---
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(6)
        self.path_label = QtWidgets.QLabel("📂 No file loaded — Press Ctrl+O to open")
        self.path_label.setStyleSheet("font-size: 13px; padding: 2px;")
        header.addWidget(self.path_label)
        self.info_label = QtWidgets.QLabel("")
        self.info_label.setStyleSheet("font-size: 12px; color: #888;")
        header.addWidget(self.info_label)
        header.addStretch()
        self.spotlight_btn = QtWidgets.QPushButton("🔆 Spotlight")
        self.spotlight_btn.setCheckable(True)
        self.spotlight_btn.setObjectName("pageBtn")
        self.spotlight_btn.setFixedWidth(100)
        self.spotlight_btn.clicked.connect(self._toggle_spotlight)
        header.addWidget(self.spotlight_btn)
        main_layout.addLayout(header)

        # --- Filter bar ---
        filter_bar = QtWidgets.QHBoxLayout()
        filter_bar.setSpacing(4)
        filter_label = QtWidgets.QLabel("🔍")
        filter_label.setFixedWidth(20)
        filter_bar.addWidget(filter_label)
        self.filter_column = QtWidgets.QComboBox()
        self.filter_column.setMinimumWidth(120)
        self.filter_column.setEditable(True)
        self.filter_column.setPlaceholderText("Column")
        filter_bar.addWidget(self.filter_column)
        self.filter_keyword = QtWidgets.QLineEdit()
        self.filter_keyword.setPlaceholderText("Filter keyword / 筛选关键词...")
        self.filter_keyword.returnPressed.connect(self._do_filter)
        filter_bar.addWidget(self.filter_keyword, stretch=1)
        self.filter_mode = QtWidgets.QComboBox()
        self.filter_mode.addItems(["contains", "equals", "regex", "search"])
        self.filter_mode.setFixedWidth(100)
        filter_bar.addWidget(self.filter_mode)
        filter_btn = QtWidgets.QPushButton("筛选 Filter")
        filter_btn.clicked.connect(self._do_filter)
        filter_btn.setFixedWidth(80)
        filter_bar.addWidget(filter_btn)
        clear_btn = QtWidgets.QPushButton("清除 Clear")
        clear_btn.setObjectName("clearBtn")
        clear_btn.clicked.connect(self._clear_filter)
        clear_btn.setFixedWidth(80)
        filter_bar.addWidget(clear_btn)
        self.result_label = QtWidgets.QLabel("")
        self.result_label.setStyleSheet("color: #1976D2; font-weight: bold; font-size: 12px;")
        self.result_label.setFixedWidth(100)
        filter_bar.addWidget(self.result_label)
        main_layout.addLayout(filter_bar)

        # --- Table (takes all remaining space) ---
        self.table = QtWidgets.QTableWidget()
        self.table.setAlternatingRowColors(True)
        self.table.setSortingEnabled(False)
        self.table.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._context_menu)
        self.table.verticalHeader().setDefaultSectionSize(24)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectionBehavior.SelectRows)
        main_layout.addWidget(self.table, stretch=1)

        # --- Pagination bar ---
        page_bar = QtWidgets.QHBoxLayout()
        page_bar.setSpacing(4)
        self.btn_first = QtWidgets.QPushButton("<<")
        self.btn_first.setObjectName("pageBtn")
        self.btn_first.setFixedWidth(36)
        self.btn_first.clicked.connect(self._page_first)
        self.btn_prev = QtWidgets.QPushButton("<")
        self.btn_prev.setObjectName("pageBtn")
        self.btn_prev.setFixedWidth(36)
        self.btn_prev.clicked.connect(self._page_prev)
        self.page_info = QtWidgets.QLabel("")
        self.page_info.setStyleSheet("font-size: 12px; padding: 0 6px;")
        self.btn_next = QtWidgets.QPushButton(">")
        self.btn_next.setObjectName("pageBtn")
        self.btn_next.setFixedWidth(36)
        self.btn_next.clicked.connect(self._page_next)
        self.btn_last = QtWidgets.QPushButton(">>")
        self.btn_last.setObjectName("pageBtn")
        self.btn_last.setFixedWidth(36)
        self.btn_last.clicked.connect(self._page_last)
        page_bar.addWidget(self.btn_first)
        page_bar.addWidget(self.btn_prev)
        page_bar.addWidget(self.page_info)
        page_bar.addWidget(self.btn_next)
        page_bar.addWidget(self.btn_last)
        page_bar.addStretch()
        self.row_count_label = QtWidgets.QLabel("")
        self.row_count_label.setStyleSheet("font-size: 12px; color: #888;")
        page_bar.addWidget(self.row_count_label)
        main_layout.addLayout(page_bar)

        self.window.statusBar().showMessage("就绪 Ready — Ctrl+O 打开文件 Open file")

    def _setup_menu(self, QtWidgets, QtGui) -> None:
        menubar = self.window.menuBar()

        file_menu = menubar.addMenu("&File")
        open_action = QtGui.QAction("&Open…", self.window)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)

        export_action = QtGui.QAction("&Export…", self.window)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._export_file)
        file_menu.addAction(export_action)

        file_menu.addSeparator()
        quit_action = QtGui.QAction("&Quit", self.window)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.window.close)
        file_menu.addAction(quit_action)

        edit_menu = menubar.addMenu("&Edit")
        copy_action = QtGui.QAction("&Copy", self.window)
        copy_action.setShortcut("Ctrl+C")
        copy_action.triggered.connect(self._copy_selection)
        edit_menu.addAction(copy_action)

        select_all_action = QtGui.QAction("Select &All", self.window)
        select_all_action.setShortcut("Ctrl+A")
        select_all_action.triggered.connect(self.table.selectAll)
        edit_menu.addAction(select_all_action)

        view_menu = menubar.addMenu("&View")
        spotlight_action = QtGui.QAction("&Spotlight 聚光灯", self.window)
        spotlight_action.setShortcut("F6")
        spotlight_action.triggered.connect(self._toggle_spotlight)
        view_menu.addAction(spotlight_action)

    def _get_page_df(self) -> pd.DataFrame | None:
        df = self.model.current_df
        if df is None:
            return None
        start = self._current_page * self._page_size
        end = min(start + self._page_size, len(df))
        return df.iloc[start:end]

    def _update_page_info(self) -> None:
        df = self.model.current_df
        if df is None:
            self.page_info.setText("")
            self.row_count_label.setText("")
            return
        total = len(df)
        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        current = self._current_page + 1
        filtered = " (filtered)" if self.model.is_filtered else ""
        self.page_info.setText(f"{current}/{total_pages}")
        self.row_count_label.setText(f"{total} rows{filtered}")

    def _page_first(self) -> None:
        self._current_page = 0
        self._refresh_table()

    def _page_prev(self) -> None:
        if self._current_page > 0:
            self._current_page -= 1
            self._refresh_table()

    def _page_next(self) -> None:
        df = self.model.current_df
        if df is None:
            return
        total_pages = max(1, (len(df) + self._page_size - 1) // self._page_size)
        if self._current_page < total_pages - 1:
            self._current_page += 1
            self._refresh_table()

    def _page_last(self) -> None:
        df = self.model.current_df
        if df is None:
            return
        total_pages = max(1, (len(df) + self._page_size - 1) // self._page_size)
        self._current_page = total_pages - 1
        self._refresh_table()

    def _refresh_table(self) -> None:
        page_df = self._get_page_df()
        if page_df is not None:
            self._load_page_to_table(page_df)
        self._update_page_info()

    def _load_page_to_table(self, df: pd.DataFrame) -> None:
        QtWidgets = self._QtWidgets
        QtCore = self._QtCore

        self.table.setRowCount(len(df))
        self.table.setColumnCount(len(df.columns))
        self.table.setHorizontalHeaderLabels(list(df.columns))

        df_reset = df.reset_index(drop=True)
        for i, col in enumerate(df_reset.columns):
            for j in range(len(df_reset)):
                val = df_reset.iloc[j, i]
                text = str(val) if pd.notna(val) else ""
                item = QtWidgets.QTableWidgetItem(text)
                item.setFlags(item.flags() & ~QtCore.Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(j, i, item)

        self.table.resizeColumnsToContents()
        self.filter_column.clear()
        self.filter_column.addItems(list(df.columns))

    def _load_data_to_table(self, df: pd.DataFrame) -> None:
        self._current_page = 0
        self._refresh_table()

    def _open_file(self) -> None:
        QtWidgets = self._QtWidgets
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            "Open Spreadsheet / 打开表格",
            "",
            "Spreadsheets (*.xlsx *.xls *.csv *.tsv *.xlsm);;"
            "All Files (*)",
        )
        if path:
            try:
                info = self.model.load(path)
                self.path_label.setText(f"📂 {Path(path).name}")
                self.info_label.setText(
                    f"{info['rows']} rows × {info['columns']} cols"
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
            self.window, "Export / 导出", "",
            "Excel (*.xlsx);;CSV (*.csv);;JSON (*.json)",
        )
        if path:
            try:
                df = self.model.current_df
                if path.endswith(".csv"):
                    df.to_csv(path, index=False)
                elif path.endswith(".json"):
                    Path(path).write_text(
                        df.to_json(orient="records", force_ascii=False)
                    )
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
            self.result_label.setText(f"{count} hits")
            self._current_page = 0
            self._load_data_to_table(self.model.current_df)
            self.window.statusBar().showMessage(
                f"Filtered: {count} rows matching '{keyword}' in '{col}'"
            )
        except Exception as e:
            self.result_label.setText(f"Error")

    def _clear_filter(self) -> None:
        self.model.clear_filter()
        self.filter_keyword.clear()
        self.result_label.setText("")
        if self.model.workbook:
            self._current_page = 0
            self._load_data_to_table(self.model.current_df)
            self.window.statusBar().showMessage("Filter cleared")

    def _toggle_spotlight(self) -> None:
        self._spotlight_active = not self._spotlight_active
        self.spotlight_btn.setChecked(self._spotlight_active)
        if self._spotlight_active:
            self.window.statusBar().showMessage("Spotlight ON — click a cell to highlight row/col")
            self.table.currentCellChanged.connect(self._apply_spotlight)
        else:
            self.window.statusBar().showMessage("Spotlight OFF")
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
        self.window.statusBar().showMessage("Copied to clipboard")

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