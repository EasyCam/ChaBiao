"""PySide6 GUI interface for ChaBiao — with i18n and theme support."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd

from .__version__ import __version__
from .core import SheetWorkbook, load_workbook
from .i18n import SUPPORTED_LANGS, detect_system_lang, t
from .theme import LIGHT_QSS, SPOTLIGHT_COLORS, THEMES

_CONFIG_DIR = Path.home() / ".chabiao"
_CONFIG_FILE = _CONFIG_DIR / "gui_config.json"

PAGE_SIZE = 500


def _load_config() -> dict[str, Any]:
    try:
        if _CONFIG_FILE.exists():
            return json.loads(_CONFIG_FILE.read_text())
    except Exception:
        pass
    return {}


def _save_config(cfg: dict[str, Any]) -> None:
    try:
        _CONFIG_DIR.mkdir(exist_ok=True)
        _CONFIG_FILE.write_text(json.dumps(cfg, indent=2))
    except Exception:
        pass


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
    """Main application window for ChaBiao GUI with i18n and theme support."""

    def __init__(self) -> None:
        QtWidgets, QtCore, QtGui = _import_pyside6()

        cfg = _load_config()
        self._lang = cfg.get("lang", detect_system_lang())
        self._theme = cfg.get("theme", "light")

        self.app = QtWidgets.QApplication(sys.argv)
        self._apply_theme()

        self.window = QtWidgets.QMainWindow()
        self.window.setWindowTitle(f"{t('app_title', self._lang)} v{__version__}")
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

    def _apply_theme(self) -> None:
        qss = THEMES.get(self._theme, LIGHT_QSS)
        self.app.setStyleSheet(qss)

    def _retranslate(self) -> None:
        lang = self._lang
        self.window.setWindowTitle(f"{t('app_title', lang)} v{__version__}")
        self.path_label.setText(t("no_file", lang))
        self.filter_keyword.setPlaceholderText(t("filter_placeholder", lang))
        self.filter_btn.setText(t("filter_btn", lang))
        self.clear_btn.setText(t("clear_btn", lang))
        self.spotlight_btn.setText(t("spotlight_btn", lang))
        self.result_label.setText("")
        self.window.statusBar().showMessage(t("status_ready", lang))

        if not self.model.workbook:
            self.info_label.setText("")
        else:
            filtered = t("filtered_suffix", lang) if self.model.is_filtered else ""
            total = len(self.model.current_df) if self.model.current_df is not None else 0
            self.row_count_label.setText(t("rows_info", lang, total=total, filtered=filtered))

        self._update_page_info()
        self._retranslate_menu()
        self._retranslate_context_menu_actions()

    def _retranslate_menu(self) -> None:
        lang = self._lang
        self._menu_file.setTitle(t("menu_file", lang))
        self._menu_edit.setTitle(t("menu_edit", lang))
        self._menu_view.setTitle(t("menu_view", lang))
        self._action_open.setText(t("menu_open", lang))
        self._action_export.setText(t("menu_export", lang))
        self._action_quit.setText(t("menu_quit", lang))
        self._action_copy.setText(t("menu_copy", lang))
        self._action_select_all.setText(t("menu_select_all", lang))
        self._action_spotlight.setText(t("menu_spotlight", lang))

        self._menu_language.setTitle(t("menu_language", lang))
        self._menu_theme.setTitle(t("menu_theme", lang))
        self._action_theme_light.setText(t("menu_theme_light", lang))
        self._action_theme_dark.setText(t("menu_theme_dark", lang))

        self._update_theme_checkmarks()
        self._update_lang_checkmarks()

    def _retranslate_context_menu_actions(self) -> None:
        lang = self._lang
        self._ctx_copy_action.setText(t("ctx_copy", lang))
        self._ctx_spotlight_action.setText(t("ctx_spotlight", lang))

    def _update_theme_checkmarks(self) -> None:
        self._action_theme_light.setChecked(self._theme == "light")
        self._action_theme_dark.setChecked(self._theme == "dark")

    def _update_lang_checkmarks(self) -> None:
        for code, action in self._lang_actions.items():
            action.setChecked(code == self._lang)

    def _setup_ui(self, QtWidgets, QtCore, QtGui) -> None:
        lang = self._lang
        central = QtWidgets.QWidget()
        self.window.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)
        main_layout.setContentsMargins(8, 4, 8, 4)
        main_layout.setSpacing(4)

        # --- Compact header: file info ---
        header = QtWidgets.QHBoxLayout()
        header.setSpacing(6)
        self.path_label = QtWidgets.QLabel(t("no_file", lang))
        self.path_label.setStyleSheet("font-size: 13px; padding: 2px;")
        header.addWidget(self.path_label)
        self.info_label = QtWidgets.QLabel("")
        self.info_label.setStyleSheet("font-size: 12px; color: #888;")
        header.addWidget(self.info_label)
        header.addStretch()
        self.spotlight_btn = QtWidgets.QPushButton(t("spotlight_btn", lang))
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
        self.filter_keyword.setPlaceholderText(t("filter_placeholder", lang))
        self.filter_keyword.returnPressed.connect(self._do_filter)
        filter_bar.addWidget(self.filter_keyword, stretch=1)
        self.filter_mode = QtWidgets.QComboBox()
        self.filter_mode.addItems(["contains", "equals", "regex", "search"])
        self.filter_mode.setFixedWidth(100)
        filter_bar.addWidget(self.filter_mode)
        self.filter_btn = QtWidgets.QPushButton(t("filter_btn", lang))
        self.filter_btn.clicked.connect(self._do_filter)
        self.filter_btn.setFixedWidth(80)
        filter_bar.addWidget(self.filter_btn)
        self.clear_btn = QtWidgets.QPushButton(t("clear_btn", lang))
        self.clear_btn.setObjectName("clearBtn")
        self.clear_btn.clicked.connect(self._clear_filter)
        self.clear_btn.setFixedWidth(80)
        filter_bar.addWidget(self.clear_btn)
        self.result_label = QtWidgets.QLabel("")
        self.result_label.setStyleSheet("font-size: 12px; font-weight: bold;")
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
        self.row_count_label.setStyleSheet("font-size: 12px;")
        page_bar.addWidget(self.row_count_label)
        main_layout.addLayout(page_bar)

        self.window.statusBar().showMessage(t("status_ready", lang))

    def _setup_menu(self, QtWidgets, QtGui) -> None:
        lang = self._lang
        menubar = self.window.menuBar()

        # File menu
        self._menu_file = menubar.addMenu(t("menu_file", lang))
        self._action_open = QtGui.QAction(t("menu_open", lang), self.window)
        self._action_open.setShortcut("Ctrl+O")
        self._action_open.triggered.connect(self._open_file)
        self._menu_file.addAction(self._action_open)

        self._action_export = QtGui.QAction(t("menu_export", lang), self.window)
        self._action_export.setShortcut("Ctrl+E")
        self._action_export.triggered.connect(self._export_file)
        self._menu_file.addAction(self._action_export)

        self._menu_file.addSeparator()
        self._action_quit = QtGui.QAction(t("menu_quit", lang), self.window)
        self._action_quit.setShortcut("Ctrl+Q")
        self._action_quit.triggered.connect(self.window.close)
        self._menu_file.addAction(self._action_quit)

        # Edit menu
        self._menu_edit = menubar.addMenu(t("menu_edit", lang))
        self._action_copy = QtGui.QAction(t("menu_copy", lang), self.window)
        self._action_copy.setShortcut("Ctrl+C")
        self._action_copy.triggered.connect(self._copy_selection)
        self._menu_edit.addAction(self._action_copy)

        self._action_select_all = QtGui.QAction(t("menu_select_all", lang), self.window)
        self._action_select_all.setShortcut("Ctrl+A")
        self._action_select_all.triggered.connect(self.table.selectAll)
        self._menu_edit.addAction(self._action_select_all)

        # View menu
        self._menu_view = menubar.addMenu(t("menu_view", lang))
        self._action_spotlight = QtGui.QAction(t("menu_spotlight", lang), self.window)
        self._action_spotlight.setShortcut("F6")
        self._action_spotlight.triggered.connect(self._toggle_spotlight)
        self._menu_view.addAction(self._action_spotlight)

        self._menu_view.addSeparator()

        # Language submenu
        self._menu_language = self._menu_view.addMenu(t("menu_language", lang))
        self._lang_actions: dict[str, QtGui.QAction] = {}
        lang_group = QtGui.QActionGroup(self.window)
        for code, name in SUPPORTED_LANGS.items():
            action = lang_group.addAction(f"{name} ({code})")
            action.setCheckable(True)
            action.setChecked(code == self._lang)
            action.triggered.connect(lambda checked, c=code: self._switch_language(c))
            self._menu_language.addAction(action)
            self._lang_actions[code] = action

        # Theme submenu
        self._menu_theme = self._menu_view.addMenu(t("menu_theme", lang))
        theme_group = QtGui.QActionGroup(self.window)
        self._action_theme_light = theme_group.addAction(t("menu_theme_light", lang))
        self._action_theme_light.setCheckable(True)
        self._action_theme_light.setChecked(self._theme == "light")
        self._action_theme_light.triggered.connect(lambda: self._switch_theme("light"))
        self._menu_theme.addAction(self._action_theme_light)

        self._action_theme_dark = theme_group.addAction(t("menu_theme_dark", lang))
        self._action_theme_dark.setCheckable(True)
        self._action_theme_dark.setChecked(self._theme == "dark")
        self._action_theme_dark.triggered.connect(lambda: self._switch_theme("dark"))
        self._menu_theme.addAction(self._action_theme_dark)

        # Context menu actions (created once, retranslated on language switch)
        self._ctx_copy_action = QtGui.QAction(t("ctx_copy", lang), self.window)
        self._ctx_copy_action.triggered.connect(self._copy_selection)
        self._ctx_spotlight_action = QtGui.QAction(t("ctx_spotlight", lang), self.window)
        self._ctx_spotlight_action.triggered.connect(self._toggle_spotlight)

    def _switch_language(self, code: str) -> None:
        self._lang = code
        self._save_settings()
        self._retranslate()

    def _switch_theme(self, theme: str) -> None:
        self._theme = theme
        self._apply_theme()
        self._save_settings()
        self._retranslate()
        if self._spotlight_active:
            self._remove_spotlight()

    def _save_settings(self) -> None:
        _save_config({"lang": self._lang, "theme": self._theme})

    def _get_page_df(self) -> pd.DataFrame | None:
        df = self.model.current_df
        if df is None:
            return None
        start = self._current_page * self._page_size
        end = min(start + self._page_size, len(df))
        return df.iloc[start:end]

    def _update_page_info(self) -> None:
        df = self.model.current_df
        lang = self._lang
        if df is None:
            self.page_info.setText("")
            self.row_count_label.setText("")
            return
        total = len(df)
        total_pages = max(1, (total + self._page_size - 1) // self._page_size)
        current = self._current_page + 1
        filtered = t("filtered_suffix", lang) if self.model.is_filtered else ""
        self.page_info.setText(f"{current}/{total_pages}")
        self.row_count_label.setText(t("rows_info", lang, total=total, filtered=filtered))

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
        lang = self._lang
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self.window,
            t("open_dialog_title", lang),
            "",
            t("open_dialog_filter", lang),
        )
        if path:
            try:
                info = self.model.load(path)
                self.path_label.setText(f"📂 {Path(path).name}")
                self.info_label.setText(f"{info['rows']} rows × {info['columns']} cols")
                self._load_data_to_table(self.model.current_df)
                self.window.statusBar().showMessage(t("loaded", lang, path=path))
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.window, t("error", lang), str(e))

    def _export_file(self) -> None:
        QtWidgets = self._QtWidgets
        lang = self._lang
        if self.model.current_df is None:
            QtWidgets.QMessageBox.warning(
                self.window, t("warning", lang), t("no_data_export", lang)
            )
            return

        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self.window,
            t("export_dialog_title", lang),
            "",
            t("export_dialog_filter", lang),
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
                self.window.statusBar().showMessage(t("exported", lang, path=path))
            except Exception as e:
                QtWidgets.QMessageBox.critical(self.window, t("error", lang), str(e))

    def _do_filter(self) -> None:
        col = self.filter_column.currentText()
        keyword = self.filter_keyword.text()
        mode = self.filter_mode.currentText()
        lang = self._lang
        if not col or not keyword:
            return
        try:
            count = self.model.set_filter(col, keyword, mode)
            self.result_label.setText(t("hits", lang, count=count))
            self._current_page = 0
            self._load_data_to_table(self.model.current_df)
            self.window.statusBar().showMessage(
                t("filtered", lang, count=count, keyword=keyword, col=col)
            )
        except Exception:
            self.result_label.setText(t("filter_error", lang))

    def _clear_filter(self) -> None:
        lang = self._lang
        self.model.clear_filter()
        self.filter_keyword.clear()
        self.result_label.setText("")
        if self.model.workbook:
            self._current_page = 0
            self._load_data_to_table(self.model.current_df)
            self.window.statusBar().showMessage(t("filter_cleared", lang))

    def _toggle_spotlight(self) -> None:
        lang = self._lang
        self._spotlight_active = not self._spotlight_active
        self.spotlight_btn.setChecked(self._spotlight_active)
        if self._spotlight_active:
            self.window.statusBar().showMessage(t("spotlight_on", lang))
            self.table.currentCellChanged.connect(self._apply_spotlight)
        else:
            self.window.statusBar().showMessage(t("spotlight_off", lang))
            try:
                self.table.currentCellChanged.disconnect(self._apply_spotlight)
            except Exception:
                pass
            self._remove_spotlight()

    def _apply_spotlight(self, row: int, col: int) -> None:
        QtGui = self._QtGui
        self._remove_spotlight()
        colors = SPOTLIGHT_COLORS.get(self._theme, SPOTLIGHT_COLORS["light"])
        light_bg = QtGui.QBrush(QtGui.QColor(*colors["row_col"]))
        focus_bg = QtGui.QBrush(QtGui.QColor(*colors["focus"]))
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
        lang = self._lang
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
        self.window.statusBar().showMessage(t("copied", lang))

    def _context_menu(self, pos) -> None:
        QtWidgets = self._QtWidgets
        menu = QtWidgets.QMenu()
        menu.addAction(self._ctx_copy_action)
        menu.addAction(self._ctx_spotlight_action)
        menu.exec(self.table.viewport().mapToGlobal(pos))

    def run(self) -> None:
        self.window.show()
        sys.exit(self.app.exec())


def main() -> None:
    window = ChaBiaoWindow()
    window.run()


if __name__ == "__main__":
    main()
